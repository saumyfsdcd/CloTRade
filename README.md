# 🚀 Live Trading System

## 📁 Project Structure

```
live_trading_system/
├── core/                    # Core trading components
│   ├── complete_trading_system.py
│   ├── hybrid_trading_system.py
│   ├── bias_analyzer.py
│   ├── fvg_detector.py
│   ├── cisd_3m_analyzer.py
│   ├── fvg_visualizer.py
│   └── config.py
├── data/                    # Data storage
│   ├── feedback_history.json
│   └── trade_history.json
├── logs/                    # Trading logs
├── backup/                  # Backup files
├── live_trader.py          # Main live trading script
├── feedback_manager.py     # Feedback management tool
└── README.md
```

## 🎯 Features

### ✅ **Feedback Learning System**
- **Automatic Learning**: System learns from trade outcomes
- **LLM Integration**: Uses feedback to improve LLM decisions
- **Performance Tracking**: Tracks accuracy and performance metrics
- **Historical Analysis**: Analyzes past decisions and outcomes

### 🔄 **Live Trading Workflow**
1. **Daily Bias Analysis** (once per day)
2. **LLM Validation** (uses feedback learning)
3. **4H FVG Monitoring** (every 4 hours)
4. **3M Continuation Analysis** (every 3 minutes)
5. **Trade Execution** (when all conditions met)

### 📊 **Real-time Monitoring**
- Continuous market monitoring
- Automatic trade execution
- Comprehensive logging
- Performance tracking

## 🚀 Quick Start

### 1. **Start Live Trading**
```bash
cd live_trading_system
python live_trader.py
```

### 2. **Check Feedback Learning**
```bash
python feedback_manager.py summary
```

### 3. **Add Trade Feedback**
```bash
python feedback_manager.py add --date 2024-12-31 --bias Buy --llm YES --outcome profitable --reason "Strong trend continuation"
```

## 📈 Feedback Learning System

### **How It Works**
1. **Trade Execution**: System executes trades based on algorithm + LLM
2. **Outcome Tracking**: You manually add trade outcomes
3. **Learning**: LLM uses feedback to improve future decisions
4. **Performance**: System tracks accuracy and learning progress

### **Feedback Commands**

#### View Summary
```bash
python feedback_manager.py summary
```

#### Add Feedback
```bash
python feedback_manager.py add \
  --date 2024-12-31 \
  --bias Buy \
  --llm YES \
  --outcome profitable \
  --reason "Strong trend continuation, good entry timing"
```

#### Export Feedback
```bash
python feedback_manager.py export --file my_feedback.json
```

#### Import Feedback
```bash
python feedback_manager.py import --file my_feedback.json
```

#### Clear Feedback (with backup)
```bash
python feedback_manager.py clear
```

## 🔧 Configuration

### **API Keys** (`core/config.py`)
```python
OPENAI_API_KEY = "your-openai-key"
POLYGON_API_KEY = "your-polygon-key"
SYMBOL = "C:XAUUSD"  # Gold
```

### **Trading Parameters**
- **Symbol**: Gold (XAUUSD)
- **Timeframes**: Daily, 4H, 3M
- **Risk-Reward**: 2:1
- **Timezone**: New York (EST)

## 📊 Monitoring

### **Live Trading Logs**
- Location: `logs/live_trading_YYYYMMDD_HHMMSS.log`
- Real-time trading activity
- Error tracking and debugging

### **Trade History**
- Location: `data/trade_history.json`
- All executed trades
- Entry, exit, and performance data

### **Feedback History**
- Location: `data/feedback_history.json`
- Learning data for LLM
- Performance metrics

## ⚠️ Important Notes

### **Safety Features**
- ✅ **No Real Money**: This is a paper trading system
- ✅ **Backup System**: Automatic backups before changes
- ✅ **Error Handling**: Comprehensive error handling
- ✅ **Logging**: Detailed logging for debugging

### **Best Practices**
1. **Start Small**: Test with small amounts first
2. **Monitor Logs**: Check logs regularly for issues
3. **Add Feedback**: Regularly add trade outcomes
4. **Backup Data**: Export feedback regularly
5. **Update APIs**: Keep API keys current

## 🔄 Workflow Details

### **Daily Bias (Step 1)**
- Runs once per day at market open
- Analyzes 30 days of daily data
- Generates Buy/Sell/Neutral bias

### **LLM Validation (Step 2)**
- Uses feedback learning from past trades
- Considers market context and bias strength
- Provides YES/NO decision with reasoning

### **4H FVG Monitoring (Step 3)**
- Checks every 4 hours for FVG retracements
- Monitors price proximity to active FVGs
- Triggers when price enters FVG zone

### **3M Continuation (Step 4)**
- Analyzes 3-minute data for continuation models
- Looks for CISD patterns after FVG retracement
- Identifies optimal entry points

### **Trade Execution (Step 5)**
- Calculates 2:1 risk-reward levels
- Places stop loss and take profit
- Records trade details for feedback

## 📞 Support

### **Common Issues**
1. **API Errors**: Check API keys and limits
2. **No Trades**: Market conditions may not meet criteria
3. **Feedback Errors**: Ensure correct date format (YYYY-MM-DD)

### **Debugging**
- Check logs in `logs/` directory
- Verify API keys in `core/config.py`
- Test individual components separately

## 🎉 Success Metrics

### **System Performance**
- **Win Rate**: Tracked in feedback summary
- **LLM Accuracy**: Learning from feedback
- **Trade Frequency**: Based on market conditions
- **Risk Management**: 2:1 risk-reward maintained

### **Learning Progress**
- **Feedback Entries**: More data = better learning
- **Accuracy Improvement**: Should improve over time
- **Decision Quality**: LLM decisions become more refined

---

**🚀 Ready to start live trading with feedback learning!** 