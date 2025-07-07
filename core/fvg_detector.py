import requests
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from config import POLYGON_API_KEY, SYMBOL

class FVGDetector:
    def __init__(self):
        self.api_key = POLYGON_API_KEY
        self.symbol = SYMBOL
    
    def get_4h_data(self, days_back=30):
        """Get 4-hour data from Polygon API"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Convert to milliseconds timestamp
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)
        
        url = f"https://api.polygon.io/v2/aggs/ticker/{self.symbol}/range/4/hour/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}?adjusted=true&sort=asc&limit=5000&apiKey={self.api_key}"
        
        print(f"📊 Fetching 4H data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        response = requests.get(url)
        data = response.json()
        results = data.get("results", [])
        
        if results:
            df = pd.DataFrame(results)
            df['timestamp'] = pd.to_datetime(df['t'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df = df.rename(columns={'o': 'Open', 'h': 'High', 'l': 'Low', 'c': 'Close', 'v': 'Volume'})
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            print(f"✅ Got {len(df)} 4H candles")
            return df
        else:
            print("❌ No 4H data received")
            return None
    
    def detect_fvgs(self, df):
        """Detect Fair Value Gaps (FVGs) in the data"""
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
                    'strength': next_candle['Low'] - prev_candle['High'],
                    'filled': False,
                    'fill_time': None
                }
                fvgs.append(fvg)
                print(f"🟢 Bullish FVG detected at {curr_candle.name}: {fvg['start_price']:.2f} - {fvg['end_price']:.2f}")
            
            # Bearish FVG: Gap between previous low and next high
            elif prev_candle['Low'] > next_candle['High']:
                fvg = {
                    'type': 'bearish',
                    'start_time': curr_candle.name,
                    'start_price': next_candle['High'],
                    'end_price': prev_candle['Low'],
                    'mid_price': (next_candle['High'] + prev_candle['Low']) / 2,
                    'strength': prev_candle['Low'] - next_candle['High'],
                    'filled': False,
                    'fill_time': None
                }
                fvgs.append(fvg)
                print(f"🔴 Bearish FVG detected at {curr_candle.name}: {fvg['start_price']:.2f} - {fvg['end_price']:.2f}")
        
        return fvgs
    
    def check_fvg_retracements(self, df, fvgs):
        """Check if price has retraced to any FVGs"""
        retracements = []
        
        for fvg in fvgs:
            if fvg['filled']:
                continue
                
            # Get data after FVG formation
            fvg_time = fvg['start_time']
            future_data = df[df.index > fvg_time]
            
            if len(future_data) == 0:
                continue
            
            # Check if price has entered the FVG zone
            for idx, candle in future_data.iterrows():
                if fvg['type'] == 'bullish':
                    # Price retraced to bullish FVG (price went down to fill the gap)
                    if candle['Low'] <= fvg['end_price'] and candle['High'] >= fvg['start_price']:
                        fvg['filled'] = True
                        fvg['fill_time'] = idx
                        retracement = {
                            'fvg': fvg,
                            'retrace_time': idx,
                            'retrace_price': candle['Close'],
                            'type': 'bullish_fvg_filled'
                        }
                        retracements.append(retracement)
                        print(f"🟢 Bullish FVG filled at {idx}: Price {candle['Close']:.2f}")
                        break
                
                elif fvg['type'] == 'bearish':
                    # Price retraced to bearish FVG (price went up to fill the gap)
                    if candle['High'] >= fvg['end_price'] and candle['Low'] <= fvg['start_price']:
                        fvg['filled'] = True
                        fvg['fill_time'] = idx
                        retracement = {
                            'fvg': fvg,
                            'retrace_time': idx,
                            'retrace_price': candle['Close'],
                            'type': 'bearish_fvg_filled'
                        }
                        retracements.append(retracement)
                        print(f"🔴 Bearish FVG filled at {idx}: Price {candle['Close']:.2f}")
                        break
        
        return retracements
    
    def get_active_fvgs(self, fvgs):
        """Get FVGs that haven't been filled yet"""
        active_fvgs = [fvg for fvg in fvgs if not fvg['filled']]
        return active_fvgs
    
    def analyze_4h_fvgs(self):
        """Complete 4H FVG analysis"""
        print("\n=== 4H FVG ANALYSIS ===")
        
        # Get 4H data
        df = self.get_4h_data(days_back=30)
        if df is None:
            return None
        
        # Detect FVGs
        fvgs = self.detect_fvgs(df)
        print(f"🎯 Detected {len(fvgs)} FVGs")
        
        # Check for retracements
        retracements = self.check_fvg_retracements(df, fvgs)
        print(f"📈 Found {len(retracements)} FVG retracements")
        
        # Get active FVGs
        active_fvgs = self.get_active_fvgs(fvgs)
        print(f"⏳ {len(active_fvgs)} FVGs still active (not filled)")
        
        # Show latest price
        latest_price = df.iloc[-1]['Close']
        print(f"💰 Current 4H price: ${latest_price:.2f}")
        
        return {
            'data': df,
            'fvgs': fvgs,
            'retracements': retracements,
            'active_fvgs': active_fvgs,
            'latest_price': latest_price
        }

# Test the FVG detector
if __name__ == "__main__":
    detector = FVGDetector()
    analysis = detector.analyze_4h_fvgs()
    
    if analysis:
        print(f"\n📊 Summary:")
        print(f"- Total FVGs: {len(analysis['fvgs'])}")
        print(f"- Filled FVGs: {len(analysis['retracements'])}")
        print(f"- Active FVGs: {len(analysis['active_fvgs'])}")
        
        if analysis['active_fvgs']:
            print(f"\n⏳ Active FVGs to monitor:")
            for fvg in analysis['active_fvgs'][-3:]:  # Show last 3
                print(f"- {fvg['type'].title()} FVG: ${fvg['start_price']:.2f} - ${fvg['end_price']:.2f}") 