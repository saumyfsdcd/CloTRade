import requests
import pandas as pd
import numpy as np
import openai
import json
from datetime import datetime, timedelta
import pytz
import time
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all components
from bias_analyzer import label_bias
from fvg_detector import FVGDetector
from cisd_3m_analyzer import CISD3MAnalyzer
from config import OPENAI_API_KEY, POLYGON_API_KEY, SYMBOL, LLM_MODEL, TEMPERATURE

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

class CompleteTradingSystem:
    def __init__(self):
        self.api_key = POLYGON_API_KEY
        self.symbol = SYMBOL
        self.ny_timezone = pytz.timezone('America/New_York')
        self.feedback_history = []
        self.load_feedback_history()
        
        # Initialize components
        self.fvg_detector = FVGDetector()
        self.cisd_analyzer = CISD3MAnalyzer()
        
        # Trading state
        self.current_bias = None
        self.llm_decision = None
        self.active_4h_fvg = None
        self.fvg_retraced = False
        self.first_cisd_found = False
        self.continuation_model = None
        self.trade_placed = False
    
    def load_feedback_history(self):
        """Load existing feedback history"""
        try:
            with open('feedback_history.json', 'r') as f:
                self.feedback_history = json.load(f)
        except FileNotFoundError:
            self.feedback_history = []
    
    def save_feedback_history(self):
        """Save feedback history"""
        with open('feedback_history.json', 'w') as f:
            json.dump(self.feedback_history, f, indent=2)
    
    def is_new_daily_candle(self):
        """Check if it's the start of a new daily candle (NY timezone)"""
        ny_time = datetime.now(self.ny_timezone)
        return ny_time.hour == 0 and ny_time.minute < 5  # Within first 5 minutes of NY day
    
    def get_daily_bias(self):
        """Step 1: Get daily bias analysis"""
        print("\n" + "="*60)
        print("🎯 STEP 1: DAILY BIAS ANALYSIS")
        print("="*60)
        
        # Get last 30 days of daily data
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        url = f"https://api.polygon.io/v2/aggs/ticker/{self.symbol}/range/1/day/{start_date}/{end_date}?adjusted=true&sort=asc&limit=5000&apiKey={self.api_key}"
        
        response = requests.get(url)
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            print("❌ No daily data received")
            return None
        
        df = pd.DataFrame(results)
        df['timestamp'] = pd.to_datetime(df['t'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df = df.rename(columns={'o': 'Open', 'h': 'High', 'l': 'Low', 'c': 'Close', 'v': 'Volume'})
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        
        # Get bias analysis
        bias_df = label_bias(df)
        if len(bias_df) == 0:
            print("❌ No bias signals generated")
            return None
        
        latest_bias = bias_df.iloc[-1]
        
        bias_data = {
            "predicted_bias": latest_bias['Bias'],
            "reason": latest_bias['Reason'],
            "htf_trend": latest_bias['HTF Trend'],
            "closure_strength": latest_bias['Closure'],
            "smt_signal": latest_bias['SMT'],
            "pd_array": latest_bias['PD Array']
        }
        
        print(f"📅 Date: {latest_bias['Date']}")
        print(f"🎯 Bias: {bias_data['predicted_bias']}")
        print(f"📊 HTF Trend: {bias_data['htf_trend']}")
        print(f"💪 Closure: {bias_data['closure_strength']}")
        print(f"🔄 SMT: {bias_data['smt_signal']}")
        print(f"💭 Reason: {bias_data['reason']}")
        
        self.current_bias = bias_data
        return bias_data
    
    def get_llm_validation(self, bias_data):
        """Step 2: Get LLM validation of bias"""
        print("\n" + "="*60)
        print("🤖 STEP 2: LLM VALIDATION")
        print("="*60)
        
        # Create context from feedback history
        feedback_context = ""
        if self.feedback_history:
            recent_feedback = self.feedback_history[-5:]
            feedback_context = "\n\nRecent Feedback Learning:\n"
            for fb in recent_feedback:
                feedback_context += f"- {fb['date']}: {fb.get('feedback_reason', '')}\n"
        
        prompt = f"""You are an expert trading advisor. Analyze this trading opportunity and provide a clear YES or NO decision.

CURRENT BIAS ANALYSIS:
- Predicted Bias: {bias_data['predicted_bias']}
- Reason: {bias_data['reason']}
- HTF Trend: {bias_data['htf_trend']}
- Closure Strength: {bias_data['closure_strength']}
- SMT Signal: {bias_data['smt_signal']}
- PD Array: {bias_data['pd_array']}

{feedback_context}

TRADING RULES:
1. Only take trades with strong confluence
2. Be conservative with conflicting signals
3. Consider recent feedback and learning
4. Risk management is priority

DECISION: Should I proceed to look for 4H FVG setups? Answer only YES or NO, followed by a brief reason.

Format your response as:
DECISION: [YES/NO]
REASON: [Brief explanation]"""

        try:
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
            
            # Parse the response
            if "DECISION:" in llm_response and "REASON:" in llm_response:
                decision_line = [line for line in llm_response.split('\n') if line.startswith('DECISION:')][0]
                reason_line = [line for line in llm_response.split('\n') if line.startswith('REASON:')][0]
                
                decision = decision_line.split('DECISION:')[1].strip()
                reason = reason_line.split('REASON:')[1].strip()
                
                llm_result = {
                    "decision": decision,
                    "reason": reason,
                    "llm_response": llm_response
                }
                
                print(f"🤖 LLM Decision: {decision}")
                print(f"💭 LLM Reason: {reason}")
                
                self.llm_decision = llm_result
                return llm_result
                
        except Exception as e:
            print(f"❌ LLM Error: {str(e)}")
            return {"decision": "ERROR", "reason": f"LLM API error: {str(e)}"}
    
    def monitor_4h_fvg(self):
        """Step 3: Monitor 4H FVG for retracement"""
        print("\n" + "="*60)
        print("🔍 STEP 3: 4H FVG MONITORING")
        print("="*60)
        
        fvg_analysis = self.fvg_detector.analyze_4h_fvgs()
        if not fvg_analysis:
            print("❌ 4H FVG analysis failed")
            return None
        
        active_fvgs = fvg_analysis['active_fvgs']
        current_price = fvg_analysis['latest_price']
        
        if not active_fvgs:
            print("⏳ No active 4H FVGs found")
            return None
        
        print(f"💰 Current 4H price: ${current_price:.2f}")
        
        # Check if price is near any active FVG
        for fvg in active_fvgs:
            fvg_range = fvg['end_price'] - fvg['start_price']
            distance_to_fvg = min(abs(current_price - fvg['start_price']), 
                                abs(current_price - fvg['end_price']))
            
            print(f"📊 {fvg['type'].title()} FVG: ${fvg['start_price']:.2f} - ${fvg['end_price']:.2f}")
            print(f"📏 Distance to FVG: ${distance_to_fvg:.2f}")
            
            # Check if price has entered the FVG zone
            if fvg['type'] == 'bullish':
                if current_price >= fvg['start_price'] and current_price <= fvg['end_price']:
                    print(f"🟢 BULLISH FVG RETRACEMENT DETECTED!")
                    self.active_4h_fvg = fvg
                    self.fvg_retraced = True
                    return fvg
            elif fvg['type'] == 'bearish':
                if current_price >= fvg['start_price'] and current_price <= fvg['end_price']:
                    print(f"🔴 BEARISH FVG RETRACEMENT DETECTED!")
                    self.active_4h_fvg = fvg
                    self.fvg_retraced = True
                    return fvg
            
            # Check if price is very close (within 10% of FVG range)
            if distance_to_fvg <= fvg_range * 0.1:
                print(f"⚠️  PRICE NEAR {fvg['type'].upper()} FVG - MONITORING...")
        
        return None
    
    def wait_for_first_cisd(self):
        """Step 4: Wait for first CISD on 3M"""
        print("\n" + "="*60)
        print("⏳ STEP 4: WAITING FOR FIRST CISD (3M)")
        print("="*60)
        
        if not self.fvg_retraced:
            print("❌ No 4H FVG retracement detected yet")
            return None
        
        print(f"🎯 4H FVG retraced: {self.active_4h_fvg['type']} at ${self.active_4h_fvg['start_price']:.2f} - ${self.active_4h_fvg['end_price']:.2f}")
        print("🔍 Looking for first CISD from initial move...")
        
        # Get 3M data and analyze
        analysis = self.cisd_analyzer.analyze_3m_continuation(self.active_4h_fvg['mid_price'])
        
        if not analysis or not analysis['first_cisd']:
            print("❌ No first CISD found yet")
            return None
        
        first_cisd = analysis['first_cisd']
        print(f"✅ FIRST CISD FOUND: {first_cisd['type'].title()} at ${first_cisd['price']:.2f}")
        
        self.first_cisd_found = True
        return first_cisd
    
    def find_continuation_model(self):
        """Step 5: Find continuation model"""
        print("\n" + "="*60)
        print("🎯 STEP 5: CONTINUATION MODEL SEARCH")
        print("="*60)
        
        if not self.first_cisd_found:
            print("❌ First CISD not found yet")
            return None
        
        print("🔍 Looking for continuation model...")
        
        # Re-analyze 3M for continuation model
        analysis = self.cisd_analyzer.analyze_3m_continuation(self.active_4h_fvg['mid_price'])
        
        if not analysis or not analysis['continuation']:
            print("⏳ Continuation model not found yet - monitoring...")
            return None
        
        continuation = analysis['continuation']
        print(f"🎯 CONTINUATION MODEL FOUND!")
        print(f"   Type: {continuation['type']}")
        print(f"   Entry: ${continuation['entry_price']:.2f}")
        print(f"   First CISD: {continuation['first_cisd']['time']} at ${continuation['first_cisd']['price']:.2f}")
        print(f"   3M FVG: {continuation['fvg']['start_time']} at ${continuation['fvg']['start_price']:.2f} - ${continuation['fvg']['end_price']:.2f}")
        print(f"   Second CISD: {continuation['second_cisd']['time']} at ${continuation['second_cisd']['price']:.2f}")
        
        self.continuation_model = continuation
        return continuation
    
    def place_trade(self, continuation):
        """Step 6: Place the trade"""
        print("\n" + "="*60)
        print("💰 STEP 6: TRADE EXECUTION")
        print("="*60)
        
        entry_price = continuation['entry_price']
        trade_type = continuation['type']
        
        # Calculate 2:1 Risk-Reward
        if trade_type == 'bearish_continuation':
            # Short trade
            stop_loss = entry_price + (entry_price - continuation['fvg']['start_price']) * 0.5
            take_profit = entry_price - (entry_price - continuation['fvg']['start_price']) * 2
            direction = "SHORT"
        else:
            # Long trade
            stop_loss = entry_price - (continuation['fvg']['end_price'] - entry_price) * 0.5
            take_profit = entry_price + (continuation['fvg']['end_price'] - entry_price) * 2
            direction = "LONG"
        
        print(f"🎯 TRADE PLACED!")
        print(f"   Direction: {direction}")
        print(f"   Entry: ${entry_price:.2f}")
        print(f"   Stop Loss: ${stop_loss:.2f}")
        print(f"   Take Profit: ${take_profit:.2f}")
        print(f"   Risk-Reward: 2:1")
        
        trade_info = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'direction': direction,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'trade_type': trade_type,
            'daily_bias': self.current_bias,
            'llm_decision': self.llm_decision,
            '4h_fvg': self.active_4h_fvg,
            'continuation_model': continuation
        }
        
        # Save trade to file
        with open('trade_history.json', 'a') as f:
            f.write(json.dumps(trade_info) + '\n')
        
        self.trade_placed = True
        return trade_info
    
    def run_complete_workflow(self):
        """Run the complete trading workflow"""
        print("\n" + "="*80)
        print("🚀 COMPLETE TRADING SYSTEM - WORKFLOW STARTED")
        print("="*80)
        
        # Check if it's new daily candle
        if not self.is_new_daily_candle():
            print("⏰ Waiting for new daily candle (NY timezone)...")
            return
        
        print("✅ New daily candle detected - starting workflow...")
        
        # Step 1: Daily Bias
        bias_data = self.get_daily_bias()
        if not bias_data:
            print("❌ Daily bias analysis failed")
            return
        
        # Step 2: LLM Validation
        llm_result = self.get_llm_validation(bias_data)
        if llm_result['decision'] != 'YES':
            print(f"❌ LLM rejected: {llm_result['reason']}")
            return
        
        print("✅ LLM approved - proceeding to 4H FVG monitoring...")
        
        # Step 3: Monitor 4H FVG
        fvg_retraced = self.monitor_4h_fvg()
        if not fvg_retraced:
            print("⏳ No 4H FVG retracement yet - monitoring...")
            return
        
        print("✅ 4H FVG retraced - switching to 3M analysis...")
        
        # Step 4: Wait for First CISD
        first_cisd = self.wait_for_first_cisd()
        if not first_cisd:
            print("⏳ First CISD not found yet - monitoring...")
            return
        
        print("✅ First CISD confirmed - looking for continuation model...")
        
        # Step 5: Find Continuation Model
        continuation = self.find_continuation_model()
        if not continuation:
            print("⏳ Continuation model not found yet - monitoring...")
            return
        
        print("✅ Continuation model found - executing trade...")
        
        # Step 6: Place Trade
        trade = self.place_trade(continuation)
        
        print("\n" + "="*80)
        print("🎉 WORKFLOW COMPLETED - TRADE EXECUTED!")
        print("="*80)

# Test the complete system
if __name__ == "__main__":
    system = CompleteTradingSystem()
    
    print("🧪 Testing Complete Trading System...")
    
    # Test individual components
    print("\n1. Testing Daily Bias...")
    bias = system.get_daily_bias()
    
    if bias:
        print("\n2. Testing LLM Validation...")
        llm_result = system.get_llm_validation(bias)
        
        if llm_result['decision'] == 'YES':
            print("\n3. Testing 4H FVG Monitoring...")
            fvg_result = system.monitor_4h_fvg()
            
            if fvg_result:
                print("\n4. Testing First CISD...")
                cisd_result = system.wait_for_first_cisd()
                
                if cisd_result:
                    print("\n5. Testing Continuation Model...")
                    continuation_result = system.find_continuation_model()
                    
                    if continuation_result:
                        print("\n6. Testing Trade Placement...")
                        trade_result = system.place_trade(continuation_result)
    
    print("\n✅ Complete system test finished!") 