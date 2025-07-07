#!/usr/bin/env python3
"""
Live Trading System
Runs continuously to monitor for trading opportunities
"""

import sys
import os
import time
import json
import logging
from datetime import datetime, timedelta
import pytz

# Add core directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

# Import trading components
from complete_trading_system import CompleteTradingSystem
from hybrid_trading_system import HybridTradingSystem
from config import SYMBOL

# Setup logging
def setup_logging():
    """Setup logging for live trading"""
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'live_trading_{timestamp}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

class LiveTrader:
    def __init__(self):
        self.logger = setup_logging()
        self.ny_timezone = pytz.timezone('America/New_York')
        
        # Initialize trading systems
        self.complete_system = CompleteTradingSystem()
        self.hybrid_system = HybridTradingSystem()
        
        # Trading state
        self.last_daily_check = None
        self.last_4h_check = None
        self.last_3m_check = None
        self.active_trades = []
        
        # Load existing trade history
        self.trade_history_file = os.path.join(os.path.dirname(__file__), 'data', 'trade_history.json')
        self.load_trade_history()
        
        self.logger.info("🚀 Live Trading System Initialized")
        self.logger.info(f"📊 Trading Symbol: {SYMBOL}")
    
    def load_trade_history(self):
        """Load existing trade history"""
        try:
            if os.path.exists(self.trade_history_file):
                with open(self.trade_history_file, 'r') as f:
                    self.trade_history = [json.loads(line) for line in f if line.strip()]
                self.logger.info(f"📈 Loaded {len(self.trade_history)} historical trades")
            else:
                self.trade_history = []
                self.logger.info("📈 No existing trade history found")
        except Exception as e:
            self.logger.error(f"❌ Error loading trade history: {e}")
            self.trade_history = []
    
    def save_trade(self, trade_info):
        """Save trade to history"""
        try:
            with open(self.trade_history_file, 'a') as f:
                f.write(json.dumps(trade_info) + '\n')
            self.trade_history.append(trade_info)
            self.logger.info(f"💾 Trade saved: {trade_info['direction']} at ${trade_info['entry_price']:.2f}")
        except Exception as e:
            self.logger.error(f"❌ Error saving trade: {e}")
    
    def check_daily_bias(self):
        """Check for new daily bias (runs once per day)"""
        ny_time = datetime.now(self.ny_timezone)
        today = ny_time.date()
        
        if self.last_daily_check == today:
            return None
        
        self.logger.info("🔍 Checking for new daily bias...")
        
        try:
            bias_data = self.complete_system.get_daily_bias()
            if bias_data:
                self.last_daily_check = today
                self.logger.info(f"✅ Daily bias: {bias_data['predicted_bias']} - {bias_data['reason']}")
                return bias_data
            else:
                self.logger.warning("⚠️ No daily bias generated")
                return None
        except Exception as e:
            self.logger.error(f"❌ Error getting daily bias: {e}")
            return None
    
    def check_llm_validation(self, bias_data):
        """Get LLM validation of bias"""
        self.logger.info("🤖 Getting LLM validation...")
        
        try:
            llm_result = self.complete_system.get_llm_validation(bias_data)
            if llm_result['decision'] == 'YES':
                self.logger.info(f"✅ LLM approved: {llm_result['reason']}")
                return llm_result
            else:
                self.logger.info(f"❌ LLM rejected: {llm_result['reason']}")
                return None
        except Exception as e:
            self.logger.error(f"❌ Error getting LLM validation: {e}")
            return None
    
    def monitor_4h_fvg(self):
        """Monitor 4H FVG for retracements (runs every 4 hours)"""
        ny_time = datetime.now(self.ny_timezone)
        current_hour = ny_time.hour
        
        # Check every 4 hours (0, 4, 8, 12, 16, 20)
        if current_hour % 4 != 0 or self.last_4h_check == current_hour:
            return None
        
        self.logger.info("🔍 Monitoring 4H FVG...")
        
        try:
            fvg_retraced = self.complete_system.monitor_4h_fvg()
            if fvg_retraced:
                self.last_4h_check = current_hour
                self.logger.info(f"✅ 4H FVG retraced: {fvg_retraced['type']} at ${fvg_retraced['start_price']:.2f}")
                return fvg_retraced
            else:
                self.logger.info("⏳ No 4H FVG retracement")
                return None
        except Exception as e:
            self.logger.error(f"❌ Error monitoring 4H FVG: {e}")
            return None
    
    def monitor_3m_continuation(self):
        """Monitor 3M for continuation models (runs every 3 minutes)"""
        ny_time = datetime.now(self.ny_timezone)
        current_minute = ny_time.minute
        
        # Check every 3 minutes
        if current_minute % 3 != 0 or self.last_3m_check == current_minute:
            return None
        
        self.logger.info("🔍 Monitoring 3M continuation...")
        
        try:
            # Check for first CISD
            first_cisd = self.complete_system.wait_for_first_cisd()
            if first_cisd:
                self.logger.info(f"✅ First CISD found: {first_cisd['type']} at ${first_cisd['price']:.2f}")
                
                # Look for continuation model
                continuation = self.complete_system.find_continuation_model()
                if continuation:
                    self.last_3m_check = current_minute
                    self.logger.info(f"✅ Continuation model found: {continuation['type']} at ${continuation['entry_price']:.2f}")
                    return continuation
                else:
                    self.logger.info("⏳ No continuation model yet")
                    return None
            else:
                self.logger.info("⏳ No first CISD yet")
                return None
        except Exception as e:
            self.logger.error(f"❌ Error monitoring 3M continuation: {e}")
            return None
    
    def execute_trade(self, continuation):
        """Execute the trade"""
        self.logger.info("💰 Executing trade...")
        
        try:
            trade_info = self.complete_system.place_trade(continuation)
            self.save_trade(trade_info)
            self.active_trades.append(trade_info)

            # --- BEGIN: ENTRY SIGNAL TERMINAL LOG ---
            self.logger.info("\n================ ENTRY SIGNAL ALERT ================")
            self.logger.info(f"📅 Time: {trade_info['timestamp']}")
            self.logger.info(f"📈 Symbol: {SYMBOL}")
            self.logger.info(f"🎯 Direction: {trade_info['direction']}")
            self.logger.info(f"💰 Entry Price: ${trade_info['entry_price']:.2f}")
            self.logger.info(f"🛑 Stop Loss: ${trade_info['stop_loss']:.2f}")
            self.logger.info(f"🎯 Take Profit: ${trade_info['take_profit']:.2f}")
            self.logger.info(f"🧠 LLM Decision: {trade_info['llm_decision']['decision']} - {trade_info['llm_decision']['reason']}")
            self.logger.info(f"📊 Bias: {trade_info['daily_bias']['predicted_bias']} - {trade_info['daily_bias']['reason']}")
            self.logger.info(f"🔍 4H FVG: {trade_info['4h_fvg']['type']} at ${trade_info['4h_fvg']['start_price']:.2f} - ${trade_info['4h_fvg']['end_price']:.2f}")
            self.logger.info(f"🔗 Continuation Model: {trade_info['trade_type']}")
            self.logger.info("====================================================\n")
            # --- END: ENTRY SIGNAL TERMINAL LOG ---

            self.logger.info(f"🎯 Trade executed: {trade_info['direction']} at ${trade_info['entry_price']:.2f}")
            self.logger.info(f"   Stop Loss: ${trade_info['stop_loss']:.2f}")
            self.logger.info(f"   Take Profit: ${trade_info['take_profit']:.2f}")
            
            return trade_info
        except Exception as e:
            self.logger.error(f"❌ Error executing trade: {e}")
            return None
    
    def add_feedback(self, trade_info, outcome, reason):
        """Add feedback for learning"""
        try:
            feedback = self.hybrid_system.add_feedback(
                date=trade_info['timestamp'].split()[0],
                algorithm_bias=trade_info['daily_bias']['predicted_bias'],
                llm_decision=trade_info['llm_decision']['decision'],
                actual_outcome=outcome,
                feedback_reason=reason
            )
            self.logger.info(f"📚 Feedback added: {outcome} - {reason}")
            return feedback
        except Exception as e:
            self.logger.error(f"❌ Error adding feedback: {e}")
            return None
    
    def get_system_status(self):
        """Get current system status"""
        ny_time = datetime.now(self.ny_timezone)
        
        status = {
            'timestamp': ny_time.strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': SYMBOL,
            'active_trades': len(self.active_trades),
            'total_trades': len(self.trade_history),
            'last_daily_check': self.last_daily_check,
            'last_4h_check': self.last_4h_check,
            'last_3m_check': self.last_3m_check
        }
        
        # Get feedback summary
        try:
            feedback_summary = self.hybrid_system.get_feedback_summary()
            status['feedback'] = feedback_summary
        except Exception as e:
            status['feedback'] = {'error': str(e)}
        
        return status
    
    def run(self):
        """Main trading loop"""
        self.logger.info("🚀 Starting live trading loop...")
        
        while True:
            try:
                # Get current time
                ny_time = datetime.now(self.ny_timezone)
                
                # Log status every hour
                if ny_time.minute == 0:
                    status = self.get_system_status()
                    self.logger.info(f"📊 System Status: {status}")
                
                # Step 1: Check daily bias (once per day)
                bias_data = self.check_daily_bias()
                
                if bias_data:
                    # Step 2: Get LLM validation
                    llm_result = self.check_llm_validation(bias_data)
                    
                    if llm_result:
                        self.logger.info("✅ Daily bias and LLM validation complete - monitoring for setups...")
                
                # Step 3: Monitor 4H FVG
                fvg_retraced = self.monitor_4h_fvg()
                
                if fvg_retraced:
                    self.logger.info("✅ 4H FVG retraced - monitoring for 3M continuation...")
                
                # Step 4: Monitor 3M continuation
                continuation = self.monitor_3m_continuation()
                
                if continuation:
                    # Step 5: Execute trade
                    trade_info = self.execute_trade(continuation)
                    
                    if trade_info:
                        self.logger.info("🎉 Trade executed successfully!")
                
                # Sleep for 1 minute before next check
                time.sleep(60)
                
            except KeyboardInterrupt:
                self.logger.info("🛑 Live trading stopped by user")
                break
            except Exception as e:
                self.logger.error(f"❌ Error in main loop: {e}")
                time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    trader = LiveTrader()
    trader.run() 