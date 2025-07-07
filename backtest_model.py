#!/usr/bin/env python3
"""
Backtest Model Runner (for live_trading_system)
Safely runs backtests using the main project's backtest_system.py
"""

import sys
import os

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from backtest_system import BacktestSystem


def main():
    # Default to 2 months if no argument provided
    months = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    print(f"\n🚀 Starting {months}-month backtest (from live_trading_system)...\n")
    backtest = BacktestSystem()
    backtest.run_backtest(months=months)

if __name__ == "__main__":
    main() 