import json
import openai
import pandas as pd
from datetime import datetime, timedelta
import requests
from config import OPENAI_API_KEY, POLYGON_API_KEY, SYMBOL, LLM_MODEL, TEMPERATURE
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import bias labeling from separate module
from bias_analyzer import label_bias
from fvg_detector import FVGDetector

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

class HybridTradingSystem:
    def __init__(self):
        self.feedback_history = []
        self.learning_data = []
        self.load_feedback_history()
    
    def load_feedback_history(self):
        """Load existing feedback history from file"""
        try:
            # Try multiple possible paths
            possible_paths = [
                'feedback_history.json',
                os.path.join(os.path.dirname(__file__), '..', 'data', 'feedback_history.json'),
                os.path.join(os.path.dirname(__file__), 'data', 'feedback_history.json')
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        self.feedback_history = json.load(f)
                    return
            
            # If no file found, start with empty list
            self.feedback_history = []
        except Exception as e:
            print(f"Warning: Could not load feedback history: {e}")
            self.feedback_history = []
    
    def save_feedback_history(self):
        """Save feedback history to file"""
        # Try to save to the data directory first
        data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'feedback_history.json')
        try:
            with open(data_path, 'w') as f:
                json.dump(self.feedback_history, f, indent=2)
        except Exception as e:
            # Fallback to current directory
            print(f"Warning: Could not save to data directory: {e}")
            with open('feedback_history.json', 'w') as f:
                json.dump(self.feedback_history, f, indent=2)
    
    def get_market_data(self, start_date, end_date):
        """Get market data from Polygon API"""
        url = f"https://api.polygon.io/v2/aggs/ticker/{SYMBOL}/range/1/day/{start_date}/{end_date}?adjusted=true&sort=asc&limit=5000&apiKey={POLYGON_API_KEY}"
        
        response = requests.get(url)
        data = response.json()
        results = data.get("results", [])
        
        if results:
            df = pd.DataFrame(results)
            df['timestamp'] = pd.to_datetime(df['t'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df.rename(columns={'o': 'Open', 'h': 'High', 'l': 'Low', 'c': 'Close', 'v': 'Volume'})
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            return df
        return None
    
    def get_llm_trading_decision(self, bias_data, market_context=""):
        """Get trading decision from LLM based on bias analysis"""
        
        # Create context from feedback history
        feedback_context = ""
        if self.feedback_history:
            recent_feedback = self.feedback_history[-5:]  # Last 5 feedback entries
            feedback_context = "\n\nRecent Feedback Learning:\n"
            for fb in recent_feedback:
                # Use the correct key for feedback
                feedback_context += f"- {fb['date']}: {fb.get('feedback_reason', '')}\n"
        
        prompt = f"""You are an expert trading advisor. Analyze this trading opportunity and provide a clear YES or NO decision.

CURRENT BIAS ANALYSIS:
- Predicted Bias: {bias_data['predicted_bias']}
- Reason: {bias_data['reason']}
- HTF Trend: {bias_data['htf_trend']}
- Closure Strength: {bias_data['closure_strength']}
- SMT Signal: {bias_data['smt_signal']}
- PD Array: {bias_data['pd_array']}

MARKET CONTEXT:
{market_context}

{feedback_context}

TRADING RULES:
1. Only take trades with strong confluence
2. Be conservative with conflicting signals
3. Consider recent feedback and learning
4. Risk management is priority

DECISION: Should I take this trade? Answer only YES or NO, followed by a brief reason.

Format your response as:
DECISION: [YES/NO]
REASON: [Brief explanation]"""

        # Show what is sent to the LLM
        print("\n--- LLM PROMPT SENT ---\n")
        print(prompt)
        print("\n--- END PROMPT ---\n")

        try:
            # Updated for openai>=1.0.0
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a conservative trading advisor focused on risk management."},
                    {"role": "user", "content": prompt}
                ],
                temperature=TEMPERATURE,
                max_tokens=150
            )
            llm_response = response.choices[0].message.content.strip()
            # Show the LLM's raw response
            print("\n--- LLM RAW RESPONSE ---\n")
            print(llm_response)
            print("\n--- END RESPONSE ---\n")
            # Parse the response
            if "DECISION:" in llm_response and "REASON:" in llm_response:
                decision_line = [line for line in llm_response.split('\n') if line.startswith('DECISION:')][0]
                reason_line = [line for line in llm_response.split('\n') if line.startswith('REASON:')][0]
                decision = decision_line.split('DECISION:')[1].strip()
                reason = reason_line.split('REASON:')[1].strip()
                return {
                    "decision": decision,
                    "reason": reason,
                    "llm_response": llm_response
                }
            else:
                return {
                    "decision": "ERROR",
                    "reason": "Could not parse LLM response",
                    "llm_response": llm_response
                }
        except Exception as e:
            # Fallback decision when LLM is unavailable
            if "insufficient_quota" in str(e) or "quota" in str(e).lower():
                fallback_decision = self.get_fallback_decision(bias_data)
                return {
                    "decision": fallback_decision["decision"],
                    "reason": f"FALLBACK: {fallback_decision['reason']} (LLM quota exceeded)",
                    "llm_response": "LLM unavailable - using fallback logic"
                }
            else:
                return {
                    "decision": "ERROR",
                    "reason": f"LLM API error: {str(e)}",
                    "llm_response": ""
                }
    
    def get_fallback_decision(self, bias_data):
        """Simple fallback decision logic when LLM is unavailable"""
        bias = bias_data['predicted_bias']
        htf_trend = bias_data['htf_trend']
        closure = bias_data['closure_strength']
        
        if bias == "Buy" and closure == "strong":
            return {"decision": "YES", "reason": "Strong buy signal with strong closure"}
        elif bias == "Sell" and closure == "strong":
            return {"decision": "NO", "reason": "Strong sell signal - avoid long positions"}
        elif bias == "Neutral":
            return {"decision": "NO", "reason": "Neutral bias - insufficient confluence"}
        else:
            return {"decision": "NO", "reason": "Weak signals - conservative approach"}
    
    def predict_next_day_with_llm(self, market_context=""):
        """Predict next day bias and get LLM decision with 4H FVG analysis"""
        print("\n=== DETAILED ANALYSIS LOG ===")
        
        # Get last 30 days of data
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        print(f"📊 Fetching data from {start_date} to {end_date}")
        
        df = self.get_market_data(start_date, end_date)
        if df is None or len(df) < 3:
            print("❌ ERROR: Insufficient data for analysis")
            return {"error": "Insufficient data for analysis"}
        
        print(f"✅ Got {len(df)} days of market data")
        print(f"📈 Latest price: ${df.iloc[-1]['Close']:.2f}")
        
        # Get bias analysis
        bias_df = label_bias(df)
        if len(bias_df) == 0:
            print("❌ ERROR: No bias signals generated")
            return {"error": "No bias signals generated"}
        
        print(f"🎯 Generated {len(bias_df)} bias signals")
        
        # Get latest bias
        latest_bias = bias_df.iloc[-1]
        print(f"📅 Latest bias date: {latest_bias['Date']}")
        print(f"🎯 Latest bias: {latest_bias['Bias']}")
        print(f"📊 HTF Trend: {latest_bias['HTF Trend']}")
        print(f"💪 Closure: {latest_bias['Closure']}")
        print(f"🔄 SMT: {latest_bias['SMT']}")
        print(f"📐 PD Array: {latest_bias['PD Array']}")
        print(f"💭 Reason: {latest_bias['Reason']}")
        
        # Calculate next working day
        next_day = datetime.now() + timedelta(days=1)
        while next_day.weekday() >= 5:  # Skip weekends
            next_day += timedelta(days=1)
        
        print(f"📅 Next working day: {next_day.strftime('%Y-%m-%d')}")
        
        # === 4H FVG ANALYSIS ===
        print(f"\n🔍 ANALYZING 4H FVGs...")
        fvg_detector = FVGDetector()
        fvg_analysis = fvg_detector.analyze_4h_fvgs()
        
        fvg_status = "No FVG analysis available"
        active_fvgs = []
        near_fvg = False
        
        if fvg_analysis:
            active_fvgs = fvg_analysis['active_fvgs']
            current_price = fvg_analysis['latest_price']
            
            if active_fvgs:
                fvg_status = f"Found {len(active_fvgs)} active FVGs"
                
                # Check if price is near any active FVG
                for fvg in active_fvgs:
                    fvg_range = fvg['end_price'] - fvg['start_price']
                    distance_to_fvg = min(abs(current_price - fvg['start_price']), 
                                        abs(current_price - fvg['end_price']))
                    
                    if distance_to_fvg <= fvg_range * 0.1:  # Within 10% of FVG range
                        near_fvg = True
                        print(f"⚠️  PRICE NEAR ACTIVE FVG: {fvg['type'].title()} FVG at ${fvg['start_price']:.2f} - ${fvg['end_price']:.2f}")
            else:
                fvg_status = "No active FVGs found"
        else:
            fvg_status = "FVG analysis failed"
        
        print(f"📊 FVG Status: {fvg_status}")
        
        # Prepare bias data for LLM
        bias_data = {
            "predicted_bias": latest_bias['Bias'],
            "reason": latest_bias['Reason'],
            "htf_trend": latest_bias['HTF Trend'],
            "closure_strength": latest_bias['Closure'],
            "smt_signal": latest_bias['SMT'],
            "pd_array": latest_bias['PD Array']
        }
        
        # Enhanced market context with FVG information
        enhanced_context = market_context
        if active_fvgs:
            enhanced_context += f"\n4H FVG Status: {len(active_fvgs)} active FVGs detected"
            if near_fvg:
                enhanced_context += " - Price near active FVG (potential retracement imminent)"
        
        print(f"\n🤖 Sending to LLM for decision...")
        print(f"📝 Enhanced market context: {enhanced_context}")
        
        # Get LLM decision
        llm_decision = self.get_llm_trading_decision(bias_data, enhanced_context)
        
        print(f"🤖 LLM Decision: {llm_decision['decision']}")
        print(f"💭 LLM Reason: {llm_decision['reason']}")
        print("=== END ANALYSIS LOG ===\n")
        
        return {
            "next_working_day": next_day.strftime("%Y-%m-%d"),
            "algorithm_bias": bias_data,
            "llm_decision": llm_decision,
            "fvg_analysis": {
                "active_fvgs": len(active_fvgs),
                "near_fvg": near_fvg,
                "fvg_status": fvg_status
            },
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def add_feedback(self, date, algorithm_bias, llm_decision, actual_outcome, feedback_reason):
        """Add feedback to improve the system"""
        print(f"\n=== FEEDBACK LOG ===")
        print(f"📅 Date: {date}")
        print(f"🎯 Algorithm Bias: {algorithm_bias}")
        print(f"🤖 LLM Decision: {llm_decision}")
        print(f"💰 Actual Outcome: {actual_outcome}")
        print(f"💭 Feedback Reason: {feedback_reason}")
        
        feedback_entry = {
            "date": date,
            "algorithm_bias": algorithm_bias,
            "llm_decision": llm_decision,
            "actual_outcome": actual_outcome,  # "profitable", "loss", "neutral"
            "feedback_reason": feedback_reason,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.feedback_history.append(feedback_entry)
        self.save_feedback_history()
        
        print(f"✅ Feedback saved. Total entries: {len(self.feedback_history)}")
        print("=== END FEEDBACK LOG ===\n")
        
        return {"status": "Feedback saved successfully", "total_feedback_entries": len(self.feedback_history)}
    
    def get_feedback_summary(self):
        """Get summary of feedback and learning"""
        if not self.feedback_history:
            return {"message": "No feedback history available"}
        
        total_feedback = len(self.feedback_history)
        profitable_decisions = len([f for f in self.feedback_history if f['actual_outcome'] == 'profitable'])
        loss_decisions = len([f for f in self.feedback_history if f['actual_outcome'] == 'loss'])
        neutral_decisions = len([f for f in self.feedback_history if f['actual_outcome'] == 'neutral'])
        
        accuracy = (profitable_decisions / total_feedback * 100) if total_feedback > 0 else 0
        
        return {
            "total_feedback_entries": total_feedback,
            "profitable_decisions": profitable_decisions,
            "loss_decisions": loss_decisions,
            "neutral_decisions": neutral_decisions,
            "accuracy_percentage": round(accuracy, 2),
            "recent_feedback": self.feedback_history[-5:] if self.feedback_history else []
        }

# For testing
if __name__ == "__main__":
    system = HybridTradingSystem()
    
    print("=== Hybrid Trading System Test ===")
    
    # Test next day prediction with LLM
    print("\n1. Next Day Prediction with LLM:")
    prediction = system.predict_next_day_with_llm("Gold showing volatility, USD strength increasing")
    print(json.dumps(prediction, indent=2))
    
    # Test feedback system
    print("\n2. Adding Sample Feedback:")
    feedback = system.add_feedback(
        date="2024-12-31",
        algorithm_bias="Buy",
        llm_decision="YES",
        actual_outcome="profitable",
        feedback_reason="Strong trend continuation, good entry timing"
    )
    print(json.dumps(feedback, indent=2))
    
    # Test feedback summary
    print("\n3. Feedback Summary:")
    summary = system.get_feedback_summary()
    print(json.dumps(summary, indent=2)) 