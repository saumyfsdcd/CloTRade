import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration
API_KEY = "HayhhX8brlW4HmWhwRoMWBhT0G0Mp3oS"
SYMBOL = "C:XAUUSD"

class CISD3MAnalyzer:
    def __init__(self):
        self.api_key = API_KEY
        self.symbol = SYMBOL
    
    def get_3m_data(self, hours_back=48):
        """Get 3-minute data from Polygon API"""
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours_back)
        
        url = f"https://api.polygon.io/v2/aggs/ticker/{self.symbol}/range/3/minute/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}?adjusted=true&sort=asc&limit=5000&apiKey={self.api_key}"
        
        print(f"📊 Fetching 3M data from {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}")
        
        response = requests.get(url)
        data = response.json()
        results = data.get("results", [])
        
        if results:
            df = pd.DataFrame(results)
            df['timestamp'] = pd.to_datetime(df['t'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df.rename(columns={'o': 'Open', 'h': 'High', 'l': 'Low', 'c': 'Close', 'v': 'Volume'})
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            print(f"✅ Got {len(df)} 3M candles")
            return df
        else:
            print("❌ No 3M data received")
            return None
    
    def detect_cisd(self, df, start_idx=0):
        """Detect Change in Structure Direction (CISD)"""
        cisd_points = []
        
        for i in range(start_idx + 2, len(df) - 2):
            prev2 = df.iloc[i - 2]
            prev1 = df.iloc[i - 1]
            curr = df.iloc[i]
            next1 = df.iloc[i + 1]
            next2 = df.iloc[i + 2]
            
            # Bullish CISD: Previous downtrend followed by higher high and higher low
            if (prev2['High'] > prev1['High'] and prev1['High'] > curr['High'] and  # Downtrend
                curr['High'] > next1['High'] and next1['High'] > next2['High'] and  # Uptrend
                curr['Low'] > next1['Low'] and next1['Low'] > next2['Low']):        # Higher lows
                
                cisd = {
                    'type': 'bullish',
                    'time': curr.name,
                    'price': curr['Close'],
                    'high': curr['High'],
                    'low': curr['Low'],
                    'confirmed': True,  # Already confirmed with 2 candles
                    'index': i
                }
                cisd_points.append(cisd)
                print(f"🟢 Bullish CISD detected at {curr.name}: ${curr['Close']:.2f}")
            
            # Bearish CISD: Previous uptrend followed by lower low and lower high
            elif (prev2['Low'] < prev1['Low'] and prev1['Low'] < curr['Low'] and  # Uptrend
                  curr['Low'] < next1['Low'] and next1['Low'] < next2['Low'] and  # Downtrend
                  curr['High'] < next1['High'] and next1['High'] < next2['High']): # Lower highs
                
                cisd = {
                    'type': 'bearish',
                    'time': curr.name,
                    'price': curr['Close'],
                    'high': curr['High'],
                    'low': curr['Low'],
                    'confirmed': True,  # Already confirmed with 2 candles
                    'index': i
                }
                cisd_points.append(cisd)
                print(f"🔴 Bearish CISD detected at {curr.name}: ${curr['Close']:.2f}")
        
        return cisd_points
    
    def detect_3m_fvgs(self, df):
        """Detect 3-minute FVGs"""
        fvgs = []
        
        for i in range(1, len(df) - 1):
            prev_candle = df.iloc[i - 1]
            curr_candle = df.iloc[i]
            next_candle = df.iloc[i + 1]
            
            # Bullish FVG: Gap between previous high and next low
            if prev_candle['High'] < next_candle['Low']:
                fvg = {
                    'type': 'bullish',
                    'start_time': curr_candle.name,
                    'start_price': prev_candle['High'],
                    'end_price': next_candle['Low'],
                    'mid_price': (prev_candle['High'] + next_candle['Low']) / 2,
                    'index': i
                }
                fvgs.append(fvg)
                print(f"🟢 3M Bullish FVG at {curr_candle.name}: {fvg['start_price']:.2f} - {fvg['end_price']:.2f}")
            
            # Bearish FVG: Gap between previous low and next high
            elif prev_candle['Low'] > next_candle['High']:
                fvg = {
                    'type': 'bearish',
                    'start_time': curr_candle.name,
                    'start_price': next_candle['High'],
                    'end_price': prev_candle['Low'],
                    'mid_price': (next_candle['High'] + prev_candle['Low']) / 2,
                    'index': i
                }
                fvgs.append(fvg)
                print(f"🔴 3M Bearish FVG at {curr_candle.name}: {fvg['start_price']:.2f} - {fvg['end_price']:.2f}")
        
        return fvgs
    
    def find_continuation_model(self, df, first_cisd, fvgs):
        """Find continuation model after first CISD"""
        if not first_cisd:
            return None
        
        # Look for continuation after the first CISD
        cisd_idx = first_cisd['index']
        continuation_data = df.iloc[cisd_idx + 2:]  # Start after CISD confirmation
        
        # Find FVGs that formed after the first CISD
        relevant_fvgs = [fvg for fvg in fvgs if fvg['index'] > cisd_idx]
        
        if not relevant_fvgs:
            print("❌ No relevant FVGs found after first CISD")
            return None
        
        # Look for second CISD at FVG
        for fvg in relevant_fvgs:
            # Check if there's a CISD at or near this FVG
            fvg_idx = fvg['index']
            
            # Look for CISD in the next few candles after FVG
            for i in range(fvg_idx + 1, min(fvg_idx + 10, len(df) - 2)):
                candle = df.iloc[i]
                
                # Check if price is at the FVG level
                if (fvg['type'] == 'bullish' and 
                    candle['Low'] <= fvg['end_price'] and candle['High'] >= fvg['start_price']):
                    
                    # Look for bearish CISD at this FVG
                    second_cisd = self.detect_cisd(df, start_idx=i)
                    if second_cisd and any(c['type'] == 'bearish' for c in second_cisd):
                        continuation = {
                            'first_cisd': first_cisd,
                            'fvg': fvg,
                            'second_cisd': second_cisd[0],
                            'entry_price': candle['Close'],
                            'type': 'bearish_continuation'
                        }
                        print(f"🎯 Bearish continuation model found!")
                        print(f"   First CISD: {first_cisd['time']} at ${first_cisd['price']:.2f}")
                        print(f"   3M FVG: {fvg['start_time']} at ${fvg['start_price']:.2f} - ${fvg['end_price']:.2f}")
                        print(f"   Second CISD: {second_cisd[0]['time']} at ${second_cisd[0]['price']:.2f}")
                        return continuation
                
                elif (fvg['type'] == 'bearish' and 
                      candle['High'] >= fvg['end_price'] and candle['Low'] <= fvg['start_price']):
                    
                    # Look for bullish CISD at this FVG
                    second_cisd = self.detect_cisd(df, start_idx=i)
                    if second_cisd and any(c['type'] == 'bullish' for c in second_cisd):
                        continuation = {
                            'first_cisd': first_cisd,
                            'fvg': fvg,
                            'second_cisd': second_cisd[0],
                            'entry_price': candle['Close'],
                            'type': 'bullish_continuation'
                        }
                        print(f"🎯 Bullish continuation model found!")
                        print(f"   First CISD: {first_cisd['time']} at ${first_cisd['price']:.2f}")
                        print(f"   3M FVG: {fvg['start_time']} at ${fvg['start_price']:.2f} - ${fvg['end_price']:.2f}")
                        print(f"   Second CISD: {second_cisd[0]['time']} at ${second_cisd[0]['price']:.2f}")
                        return continuation
        
        print("❌ No continuation model found")
        return None
    
    def analyze_3m_continuation(self, fvg_retracement_price):
        """Complete 3M continuation analysis"""
        print(f"\n=== 3M CONTINUATION ANALYSIS ===")
        print(f"🎯 Analyzing from 4H FVG retracement price: ${fvg_retracement_price:.2f}")
        
        # Get 3M data
        df = self.get_3m_data(hours_back=48)
        if df is None:
            return None
        
        # Detect first CISD (from initial move down)
        print(f"\n🔍 Looking for first CISD from initial move...")
        first_cisds = self.detect_cisd(df)
        
        if not first_cisds:
            print("❌ No CISD detected")
            return None
        
        # Get the most recent CISD as the first CISD
        first_cisd = first_cisds[-1]
        print(f"✅ First CISD found: {first_cisd['type'].title()} at ${first_cisd['price']:.2f}")
        
        # Detect 3M FVGs
        print(f"\n🔍 Looking for 3M FVGs...")
        fvgs = self.detect_3m_fvgs(df)
        
        # Find continuation model
        print(f"\n🔍 Looking for continuation model...")
        continuation = self.find_continuation_model(df, first_cisd, fvgs)
        
        return {
            'data': df,
            'first_cisd': first_cisd,
            'fvgs': fvgs,
            'continuation': continuation,
            'latest_price': df.iloc[-1]['Close']
        }

# Test the 3M analyzer
if __name__ == "__main__":
    analyzer = CISD3MAnalyzer()
    
    # Test with a sample FVG retracement price
    test_retracement_price = 3333.32  # Current price near the active 4H FVG
    analysis = analyzer.analyze_3m_continuation(test_retracement_price)
    
    if analysis:
        print(f"\n📊 3M Analysis Summary:")
        print(f"First CISD: {analysis['first_cisd']['type']} at ${analysis['first_cisd']['price']:.2f}")
        print(f"3M FVGs found: {len(analysis['fvgs'])}")
        print(f"Continuation model: {'Found' if analysis['continuation'] else 'Not found'}")
        print(f"Latest 3M price: ${analysis['latest_price']:.2f}")
        
        if analysis['continuation']:
            print(f"\n🎯 TRADE SETUP:")
            print(f"Entry: ${analysis['continuation']['entry_price']:.2f}")
            print(f"Type: {analysis['continuation']['type']}")
            print(f"Risk-Reward: 2:1") 