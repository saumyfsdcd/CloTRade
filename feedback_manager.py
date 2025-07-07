#!/usr/bin/env python3
"""
Feedback Management System
Manages and analyzes feedback learning data
"""

import sys
import os
import json
from datetime import datetime
import argparse

# Add core directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from hybrid_trading_system import HybridTradingSystem

class FeedbackManager:
    def __init__(self):
        self.hybrid_system = HybridTradingSystem()
        self.feedback_file = os.path.join(os.path.dirname(__file__), 'data', 'feedback_history.json')
        # Update the hybrid system to use the correct feedback file path
        self.hybrid_system.feedback_history = []
        self.hybrid_system.load_feedback_history()
    
    def show_feedback_summary(self):
        """Show feedback summary"""
        print("\n" + "="*60)
        print("📊 FEEDBACK LEARNING SUMMARY")
        print("="*60)
        
        summary = self.hybrid_system.get_feedback_summary()
        
        if 'message' in summary:
            print(f"❌ {summary['message']}")
            return
        
        print(f"📈 Total Feedback Entries: {summary['total_feedback_entries']}")
        print(f"✅ Profitable Decisions: {summary['profitable_decisions']}")
        print(f"❌ Loss Decisions: {summary['loss_decisions']}")
        print(f"⚖️ Neutral Decisions: {summary['neutral_decisions']}")
        print(f"🎯 Accuracy: {summary['accuracy_percentage']}%")
        
        print(f"\n📝 Recent Feedback:")
        for fb in summary['recent_feedback']:
            print(f"   {fb['date']}: {fb['algorithm_bias']} | {fb['llm_decision']} | {fb['actual_outcome']}")
            print(f"      Reason: {fb['feedback_reason']}")
    
    def add_feedback(self, date, algorithm_bias, llm_decision, actual_outcome, feedback_reason):
        """Add new feedback"""
        print(f"\n📝 Adding Feedback...")
        print(f"   Date: {date}")
        print(f"   Algorithm Bias: {algorithm_bias}")
        print(f"   LLM Decision: {llm_decision}")
        print(f"   Actual Outcome: {actual_outcome}")
        print(f"   Reason: {feedback_reason}")
        
        result = self.hybrid_system.add_feedback(
            date=date,
            algorithm_bias=algorithm_bias,
            llm_decision=llm_decision,
            actual_outcome=actual_outcome,
            feedback_reason=feedback_reason
        )
        
        print(f"✅ {result['status']}")
        print(f"📊 Total entries: {result['total_feedback_entries']}")
    
    def export_feedback(self, filename=None):
        """Export feedback data"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"feedback_export_{timestamp}.json"
        
        try:
            with open(self.feedback_file, 'r') as f:
                feedback_data = json.load(f)
            
            export_path = os.path.join(os.path.dirname(__file__), 'backup', filename)
            with open(export_path, 'w') as f:
                json.dump(feedback_data, f, indent=2)
            
            print(f"✅ Feedback exported to: {export_path}")
            print(f"📊 Exported {len(feedback_data)} entries")
            
        except Exception as e:
            print(f"❌ Error exporting feedback: {e}")
    
    def import_feedback(self, filename):
        """Import feedback data"""
        try:
            import_path = os.path.join(os.path.dirname(__file__), 'backup', filename)
            
            with open(import_path, 'r') as f:
                feedback_data = json.load(f)
            
            # Backup current feedback
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(os.path.dirname(__file__), 'backup', f"feedback_backup_{timestamp}.json")
            
            with open(self.feedback_file, 'r') as f:
                current_data = json.load(f)
            
            with open(backup_path, 'w') as f:
                json.dump(current_data, f, indent=2)
            
            # Import new data
            with open(self.feedback_file, 'w') as f:
                json.dump(feedback_data, f, indent=2)
            
            print(f"✅ Feedback imported from: {import_path}")
            print(f"📊 Imported {len(feedback_data)} entries")
            print(f"💾 Current feedback backed up to: {backup_path}")
            
        except Exception as e:
            print(f"❌ Error importing feedback: {e}")
    
    def clear_feedback(self):
        """Clear all feedback data"""
        confirm = input("⚠️ Are you sure you want to clear all feedback data? (yes/no): ")
        if confirm.lower() == 'yes':
            try:
                # Backup before clearing
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = os.path.join(os.path.dirname(__file__), 'backup', f"feedback_backup_{timestamp}.json")
                
                with open(self.feedback_file, 'r') as f:
                    current_data = json.load(f)
                
                with open(backup_path, 'w') as f:
                    json.dump(current_data, f, indent=2)
                
                # Clear feedback
                with open(self.feedback_file, 'w') as f:
                    json.dump([], f, indent=2)
                
                print(f"✅ Feedback cleared")
                print(f"💾 Backup saved to: {backup_path}")
                
            except Exception as e:
                print(f"❌ Error clearing feedback: {e}")
        else:
            print("❌ Operation cancelled")

def main():
    parser = argparse.ArgumentParser(description='Feedback Management System')
    parser.add_argument('action', choices=['summary', 'add', 'export', 'import', 'clear'], 
                       help='Action to perform')
    parser.add_argument('--date', help='Date for feedback (YYYY-MM-DD)')
    parser.add_argument('--bias', choices=['Buy', 'Sell', 'Neutral'], help='Algorithm bias')
    parser.add_argument('--llm', choices=['YES', 'NO'], help='LLM decision')
    parser.add_argument('--outcome', choices=['profitable', 'loss', 'neutral'], help='Actual outcome')
    parser.add_argument('--reason', help='Feedback reason')
    parser.add_argument('--file', help='File name for export/import')
    
    args = parser.parse_args()
    
    manager = FeedbackManager()
    
    if args.action == 'summary':
        manager.show_feedback_summary()
    
    elif args.action == 'add':
        if not all([args.date, args.bias, args.llm, args.outcome, args.reason]):
            print("❌ All arguments required for add: --date, --bias, --llm, --outcome, --reason")
            return
        
        manager.add_feedback(
            date=args.date,
            algorithm_bias=args.bias,
            llm_decision=args.llm,
            actual_outcome=args.outcome,
            feedback_reason=args.reason
        )
    
    elif args.action == 'export':
        manager.export_feedback(args.file)
    
    elif args.action == 'import':
        if not args.file:
            print("❌ File name required for import: --file")
            return
        manager.import_feedback(args.file)
    
    elif args.action == 'clear':
        manager.clear_feedback()

if __name__ == "__main__":
    main() 