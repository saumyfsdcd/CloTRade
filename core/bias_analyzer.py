import pandas as pd

def label_bias(df):
    """Bias labeling function extracted from claude.py"""
    labels = []
    for i in range(2, len(df)):
        prev2 = df.iloc[i - 2]
        prev1 = df.iloc[i - 1]
        curr = df.iloc[i]
        
        # HTF trend logic (2-day trend)
        htf_trend = "up" if prev2['Close'] < prev1['Close'] else "down"
        
        # Closures
        close_strength = "strong" if abs(curr['Close'] - curr['Open']) > 0.5 * (curr['High'] - curr['Low']) else "weak"
        
        # Simple SMT-like logic (fake: use close divergence as a placeholder)
        smt_div = "bullish" if prev1['Close'] < curr['Close'] and prev1['Low'] > curr['Low'] else \
                 "bearish" if prev1['Close'] > curr['Close'] and prev1['High'] < curr['High'] else "neutral"
        
        # PD array logic: FVG-style fake condition
        pd_array = "retraced" if curr['Low'] < prev1['Low'] or curr['High'] > prev1['High'] else "none"
        
        # Final bias logic with SMT as confluence
        reason = ""
        if htf_trend == "up" and close_strength == "strong":
            if smt_div == "bullish":
                label = "Buy"
                reason = f"Strong bullish confluence: HTF trend UP + Strong closure + Bullish SMT divergence"
            elif smt_div == "neutral":
                label = "Buy"  # Still buy but weaker confluence
                reason = f"Moderate bullish signal: HTF trend UP + Strong closure (SMT neutral)"
            else:
                label = "Neutral"  # SMT bearish conflicts with up trend
                reason = f"Conflicting signals: HTF trend UP + Strong closure but SMT bearish divergence"
        elif htf_trend == "down" and close_strength == "strong":
            if smt_div == "bearish":
                label = "Sell"
                reason = f"Strong bearish confluence: HTF trend DOWN + Strong closure + Bearish SMT divergence"
            elif smt_div == "neutral":
                label = "Sell"  # Still sell but weaker confluence
                reason = f"Moderate bearish signal: HTF trend DOWN + Strong closure (SMT neutral)"
            else:
                label = "Neutral"  # SMT bullish conflicts with down trend
                reason = f"Conflicting signals: HTF trend DOWN + Strong closure but SMT bullish divergence"
        else:
            label = "Neutral"
            if close_strength == "weak":
                reason = f"Weak closure ({close_strength}) - insufficient momentum for clear bias"
            else:
                reason = f"Mixed conditions: HTF trend {htf_trend.upper()}, closure {close_strength}"
        
        labels.append({
            "Date": curr.name.date(),
            "HTF Trend": htf_trend,
            "Closure": close_strength,
            "SMT": smt_div,
            "PD Array": pd_array,
            "Bias": label,
            "Reason": reason
        })
    
    return pd.DataFrame(labels) 