#!/usr/bin/env python3
"""
Live Trading System Startup
Simple menu to start live trading or manage feedback
"""

import os
import sys
import subprocess
from datetime import datetime

def print_banner():
    """Print startup banner"""
    print("\n" + "="*60)
    print("🚀 LIVE TRADING SYSTEM")
    print("="*60)
    print("📊 Symbol: Gold (XAUUSD)")
    print("🤖 AI-Powered with Feedback Learning")
    print("⏰ Real-time Market Monitoring")
    print("="*60)

def check_dependencies():
    """Check if required files exist"""
    required_files = [
        'core/config.py',
        'core/complete_trading_system.py',
        'core/hybrid_trading_system.py',
        'data/feedback_history.json'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    return True

def show_menu():
    """Show main menu"""
    print("\n📋 MAIN MENU:")
    print("1. 🚀 Start Live Trading")
    print("2. 📊 View Feedback Summary")
    print("3. 📝 Add Trade Feedback")
    print("4. 💾 Export Feedback Data")
    print("5. 📈 View System Status")
    print("6. 🔧 Test Individual Components")
    print("7. ❌ Exit")
    
    choice = input("\nSelect option (1-7): ").strip()
    return choice

def start_live_trading():
    """Start the live trading system"""
    print("\n🚀 Starting Live Trading System...")
    print("📝 Logs will be saved to logs/ directory")
    print("⏹️  Press Ctrl+C to stop")
    print("-" * 40)
    
    try:
        subprocess.run([sys.executable, 'live_trader.py'], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Live trading stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting live trading: {e}")

def view_feedback_summary():
    """View feedback learning summary"""
    print("\n📊 Loading Feedback Summary...")
    try:
        subprocess.run([sys.executable, 'feedback_manager.py', 'summary'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error loading feedback summary: {e}")

def add_feedback():
    """Add trade feedback"""
    print("\n📝 Adding Trade Feedback")
    print("Enter the following information:")
    
    date = input("Date (YYYY-MM-DD): ").strip()
    bias = input("Algorithm Bias (Buy/Sell/Neutral): ").strip()
    llm = input("LLM Decision (YES/NO): ").strip()
    outcome = input("Actual Outcome (profitable/loss/neutral): ").strip()
    reason = input("Feedback Reason: ").strip()
    
    if not all([date, bias, llm, outcome, reason]):
        print("❌ All fields are required")
        return
    
    try:
        cmd = [
            sys.executable, 'feedback_manager.py', 'add',
            '--date', date,
            '--bias', bias,
            '--llm', llm,
            '--outcome', outcome,
            '--reason', reason
        ]
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error adding feedback: {e}")

def export_feedback():
    """Export feedback data"""
    filename = input("Export filename (optional, press Enter for auto): ").strip()
    
    try:
        cmd = [sys.executable, 'feedback_manager.py', 'export']
        if filename:
            cmd.extend(['--file', filename])
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error exporting feedback: {e}")

def view_system_status():
    """View system status"""
    print("\n📈 SYSTEM STATUS")
    print("-" * 40)
    
    # Check file sizes
    feedback_file = 'data/feedback_history.json'
    if os.path.exists(feedback_file):
        size = os.path.getsize(feedback_file)
        print(f"📊 Feedback History: {size} bytes")
    
    # Check logs directory
    logs_dir = 'logs'
    if os.path.exists(logs_dir):
        log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log')]
        print(f"📝 Log Files: {len(log_files)} files")
    
    # Check backup directory
    backup_dir = 'backup'
    if os.path.exists(backup_dir):
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.json')]
        print(f"💾 Backup Files: {len(backup_files)} files")
    
    print(f"⏰ Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def test_components():
    """Test individual components"""
    print("\n🔧 Testing Components")
    print("-" * 40)
    
    components = [
        ('Bias Analyzer', 'core/bias_analyzer.py'),
        ('FVG Detector', 'core/fvg_detector.py'),
        ('CISD Analyzer', 'core/cisd_3m_analyzer.py'),
        ('Hybrid System', 'core/hybrid_trading_system.py')
    ]
    
    for name, file in components:
        if os.path.exists(file):
            print(f"✅ {name}: {file}")
        else:
            print(f"❌ {name}: {file} (missing)")

def main():
    """Main function"""
    print_banner()
    
    if not check_dependencies():
        print("\n❌ Please ensure all required files are present")
        return
    
    while True:
        choice = show_menu()
        
        if choice == '1':
            start_live_trading()
        elif choice == '2':
            view_feedback_summary()
        elif choice == '3':
            add_feedback()
        elif choice == '4':
            export_feedback()
        elif choice == '5':
            view_system_status()
        elif choice == '6':
            test_components()
        elif choice == '7':
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-7.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main() 