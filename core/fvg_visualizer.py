import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np
from datetime import datetime, timedelta

# Configuration
API_KEY = "HayhhX8brlW4HmWhwRoMWBhT0G0Mp3oS"
SYMBOL = "C:XAUUSD"

class FVGVisualizer:
    def __init__(self):
        self.api_key = API_KEY
        self.symbol = SYMBOL
    
    def get_4h_data(self, days_back=30):
        """Get 4-hour data from Polygon API"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
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
    
    def plot_candles_with_fvgs(self, df, fvgs):
        """Plot candlesticks with FVG markings"""
        fig, ax = plt.subplots(figsize=(15, 8))
        fig.patch.set_facecolor('black')
        ax.set_facecolor('black')
        
        # Plot candlesticks
        for i, (date, row) in enumerate(df.iterrows()):
            color = 'green' if row['Close'] > row['Open'] else 'red'
            
            # Candlestick body
            body_height = abs(row['Close'] - row['Open'])
            body_bottom = min(row['Open'], row['Close'])
            
            # Draw the body
            rect = Rectangle((i, body_bottom), 0.8, body_height, 
                            facecolor=color, edgecolor=color, alpha=0.7)
            ax.add_patch(rect)
            
            # Draw the wicks
            ax.plot([i+0.4, i+0.4], [row['Low'], row['High']], 
                   color=color, linewidth=1)
        
        # Plot FVGs
        for fvg in fvgs:
            fvg_idx = df.index.get_loc(fvg['start_time'])
            
            if fvg['type'] == 'bullish':
                # Bullish FVG - green rectangle
                fvg_height = fvg['end_price'] - fvg['start_price']
                fvg_rect = Rectangle((fvg_idx, fvg['start_price']), 2, fvg_height,
                                   facecolor='lightgreen', edgecolor='green', 
                                   alpha=0.3, linewidth=2, linestyle='--')
                ax.add_patch(fvg_rect)
                
                # Add FVG label
                ax.text(fvg_idx + 1, fvg['mid_price'], 'BULLISH FVG', 
                       color='green', fontsize=8, ha='center', va='center',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='green', alpha=0.7))
                
            elif fvg['type'] == 'bearish':
                # Bearish FVG - red rectangle
                fvg_height = fvg['end_price'] - fvg['start_price']
                fvg_rect = Rectangle((fvg_idx, fvg['start_price']), 2, fvg_height,
                                   facecolor='lightcoral', edgecolor='red', 
                                   alpha=0.3, linewidth=2, linestyle='--')
                ax.add_patch(fvg_rect)
                
                # Add FVG label
                ax.text(fvg_idx + 1, fvg['mid_price'], 'BEARISH FVG', 
                       color='red', fontsize=8, ha='center', va='center',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor='red', alpha=0.7))
        
        # Styling
        ax.set_title('Gold (XAU/USD) 4H Chart with FVG Markings', color='white', fontsize=16, pad=20)
        ax.set_ylabel('Price ($)', color='white', fontsize=12)
        ax.set_xlabel('Date', color='white', fontsize=12)
        
        # Set x-axis labels
        num_ticks = min(10, len(df))
        tick_indices = np.linspace(0, len(df)-1, num_ticks, dtype=int)
        tick_labels = [df.index[i].strftime('%m-%d %H:%M') for i in tick_indices]
        ax.set_xticks(tick_indices)
        ax.set_xticklabels(tick_labels, rotation=45, ha='right', color='white')
        
        # Grid and colors
        ax.grid(True, alpha=0.3, color='gray')
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['top'].set_color('white')
        ax.spines['right'].set_color('white')
        ax.spines['left'].set_color('white')
        
        # Legend
        legend_elements = [
            plt.Rectangle((0,0),1,1, facecolor='lightgreen', alpha=0.3, edgecolor='green', label='Bullish FVG'),
            plt.Rectangle((0,0),1,1, facecolor='lightcoral', alpha=0.3, edgecolor='red', label='Bearish FVG')
        ]
        ax.legend(handles=legend_elements, loc='upper left', 
                  facecolor='black', edgecolor='white', labelcolor='white')
        
        plt.tight_layout()
        plt.show()
        
        # Print FVG summary
        print(f"\n📊 FVG Summary:")
        print(f"Total FVGs: {len(fvgs)}")
        active_fvgs = [fvg for fvg in fvgs if not fvg['filled']]
        filled_fvgs = [fvg for fvg in fvgs if fvg['filled']]
        print(f"Active FVGs: {len(active_fvgs)}")
        print(f"Filled FVGs: {len(filled_fvgs)}")
        
        if active_fvgs:
            print(f"\n⏳ Active FVGs:")
            for fvg in active_fvgs:
                print(f"- {fvg['type'].title()} FVG: ${fvg['start_price']:.2f} - ${fvg['end_price']:.2f}")

# Test the visualizer
if __name__ == "__main__":
    visualizer = FVGVisualizer()
    
    # Get data
    df = visualizer.get_4h_data(days_back=30)
    if df is not None:
        # Detect FVGs
        fvgs = visualizer.detect_fvgs(df)
        
        # Check retracements
        retracements = visualizer.check_fvg_retracements(df, fvgs)
        
        # Plot the chart
        visualizer.plot_candles_with_fvgs(df, fvgs) 