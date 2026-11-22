"""Tab 1: classic indicator analysis (EMA, RSI, MACD, BB, ATR, stochastic, patterns)."""
import numpy as np
import pandas as pd

from data import convert_numpy_types


def calculate_ema(prices, period):
    return prices.ewm(span=period, adjust=False).mean()

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(prices, fast=12, slow=26, signal=9):
    ef = calculate_ema(prices, fast)
    es = calculate_ema(prices, slow)
    ml = ef - es
    sl = calculate_ema(ml, signal)
    return ml, sl, ml - sl

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    m = prices.rolling(window=period).mean()
    s = prices.rolling(window=period).std()
    return m + (s * std_dev), m, m - (s * std_dev)

def calculate_atr_pandas(high, low, close, period=14):
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def calculate_stochastic(high, low, close, period=14, sk=3, sd=3):
    ll = low.rolling(window=period).min()
    hh = high.rolling(window=period).max()
    k = 100 * ((close - ll) / (hh - ll))
    k = k.rolling(window=sk).mean()
    d = k.rolling(window=sd).mean()
    return k, d

def find_support_resistance(df, window=20):
    highs = df['High'].values
    lows = df['Low'].values
    res = []
    sup = []
    for i in range(window, len(highs) - window):
        if highs[i] == max(highs[i-window:i+window]):
            res.append(highs[i])
        if lows[i] == min(lows[i-window:i+window]):
            sup.append(lows[i])
    return sorted(list(set(sup)))[:5], sorted(list(set(res)), reverse=True)[:5]

def detect_chart_patterns(df):
    patterns = []
    close = df['Close'].values
    high = df['High'].values
    low = df['Low'].values
    if len(close) < 100:
        return patterns
    cp = close[-1]

    recent_lows = []
    for i in range(20, len(low) - 20):
        if low[i] == min(low[i-20:i+20]):
            recent_lows.append((i, low[i]))
    if len(recent_lows) >= 2:
        if abs(recent_lows[-1][1] - recent_lows[-2][1]) / recent_lows[-2][1] < 0.02:
            ep = recent_lows[-1][1] * 1.02
            sl = recent_lows[-1][1] * 0.98
            r = ep - sl
            patterns.append({'name': 'Double Bottom', 'type': 'reversal', 'direction': 'bullish',
                'confidence': 85, 'entry_condition': f'price > {ep:.5f}', 'stop_loss': f'price < {sl:.5f}',
                'take_profit_1': f'{ep+r*2:.5f} (1:2 RR)', 'take_profit_2': f'{ep+r*3:.5f} (1:3 RR)'})

    peaks = []
    for i in range(20, len(high) - 20):
        if high[i] == max(high[i-20:i+20]):
            peaks.append((i, high[i]))
    if len(peaks) >= 3:
        if peaks[-2][1] > peaks[-1][1] and peaks[-2][1] > peaks[-3][1]:
            ep = peaks[-1][1] * 0.98
            sl = peaks[-2][1]
            r = sl - ep
            patterns.append({'name': 'Head and Shoulders', 'type': 'reversal', 'direction': 'bearish',
                'confidence': 80, 'entry_condition': f'price < {ep:.5f}', 'stop_loss': f'price > {sl:.5f}',
                'take_profit_1': f'{ep-r*2:.5f} (1:2 RR)', 'take_profit_2': f'{ep-r*3:.5f} (1:3 RR)'})

    if len(close) > 30:
        rt = (close[-1] - close[-30]) / close[-30]
        con = np.std(close[-10:]) / np.mean(close[-10:])
        if abs(rt) > 0.05 and con < 0.02:
            d = 'bullish' if rt > 0 else 'bearish'
            if d == 'bullish':
                ep, sl = cp*1.01, cp*0.98; r = ep-sl
                patterns.append({'name': 'Flag Pattern', 'type': 'continuation', 'direction': d,
                    'confidence': 70, 'entry_condition': f'price > {ep:.5f}', 'stop_loss': f'price < {sl:.5f}',
                    'take_profit_1': f'{ep+r*2:.5f} (1:2 RR)', 'take_profit_2': f'{ep+r*3:.5f} (1:3 RR)'})
            else:
                ep, sl = cp*0.99, cp*1.02; r = sl-ep
                patterns.append({'name': 'Flag Pattern', 'type': 'continuation', 'direction': d,
                    'confidence': 70, 'entry_condition': f'price < {ep:.5f}', 'stop_loss': f'price > {sl:.5f}',
                    'take_profit_1': f'{ep-r*2:.5f} (1:2 RR)', 'take_profit_2': f'{ep-r*3:.5f} (1:3 RR)'})
    return patterns

def generate_trading_signals(analysis):
    signals = {'primary_signal': 'NEUTRAL', 'strength': 0, 'entry_points': [], 'stop_loss': None, 'take_profit': []}
    bs, ss = 0, 0
    if analysis['trend'] == 'Bullish': bs += 2
    elif analysis['trend'] == 'Bearish': ss += 2
    if analysis['rsi'] < 30: bs += 2; signals['entry_points'].append(f"RSI oversold at {analysis['rsi']}")
    elif analysis['rsi'] > 70: ss += 2; signals['entry_points'].append(f"RSI overbought at {analysis['rsi']}")
    if analysis['macd'] > analysis['macd_signal']: bs += 1
    else: ss += 1
    if analysis['current_price'] > analysis['ema_20']: bs += 1
    else: ss += 1
    if analysis['current_price'] < analysis['bb_lower']: bs += 2; signals['entry_points'].append("Price at lower BB")
    elif analysis['current_price'] > analysis['bb_upper']: ss += 2; signals['entry_points'].append("Price at upper BB")
    if analysis['stochastic']['k'] < 20: bs += 1; signals['entry_points'].append(f"Stochastic oversold")
    elif analysis['stochastic']['k'] > 80: ss += 1; signals['entry_points'].append(f"Stochastic overbought")
    if analysis.get('volume_ratio', 1) > 1.5:
        bs += 1; ss += 1; signals['entry_points'].append(f"Volume {analysis.get('volume_ratio',1):.2f}x avg")
    for p in analysis['patterns']:
        if p['direction'] == 'bullish': bs += 2; signals['entry_points'].append(p['name'])
        elif p['direction'] == 'bearish': ss += 2; signals['entry_points'].append(p['name'])
    if bs > ss + 2: signals['primary_signal'] = 'STRONG BUY'; signals['strength'] = min(bs, 10)
    elif bs > ss: signals['primary_signal'] = 'BUY'; signals['strength'] = min(bs, 10)
    elif ss > bs + 2: signals['primary_signal'] = 'STRONG SELL'; signals['strength'] = min(ss, 10)
    elif ss > bs: signals['primary_signal'] = 'SELL'; signals['strength'] = min(ss, 10)
    atr = analysis['atr']
    if 'BUY' in signals['primary_signal']:
        signals['stop_loss'] = round(analysis['current_price'] - atr*2, 5)
        signals['take_profit'] = [round(analysis['current_price'] + atr*x, 5) for x in [1.5, 3, 5]]
    elif 'SELL' in signals['primary_signal']:
        signals['stop_loss'] = round(analysis['current_price'] + atr*2, 5)
        signals['take_profit'] = [round(analysis['current_price'] - atr*x, 5) for x in [1.5, 3, 5]]
    return signals

def analyze_market(df, symbol):
    if df is None or df.empty:
        return None
    try:
        close = df['Close']; high = df['High']; low = df['Low']; volume = df['Volume']
        ema_20 = calculate_ema(close, 20); ema_50 = calculate_ema(close, 50); ema_200 = calculate_ema(close, 200)
        rsi = calculate_rsi(close)
        macd, macd_sig, macd_hist = calculate_macd(close)
        bb_u, bb_m, bb_l = calculate_bollinger_bands(close)
        atr = calculate_atr_pandas(high, low, close)
        stk, std = calculate_stochastic(high, low, close)
        sup, res = find_support_resistance(df)
        patterns = detect_chart_patterns(df)
        avg_vol = volume.mean()
        vr = volume.iloc[-1] / avg_vol if avg_vol > 0 else 1
        cp = close.iloc[-1]
        trend = "Neutral"
        if cp > ema_50.iloc[-1] and ema_20.iloc[-1] > ema_50.iloc[-1]: trend = "Bullish"
        elif cp < ema_50.iloc[-1] and ema_20.iloc[-1] < ema_50.iloc[-1]: trend = "Bearish"
        c24 = ((cp - close.iloc[-24]) / close.iloc[-24] * 100) if len(close) > 24 else 0
        c7d = ((cp - close.iloc[-168]) / close.iloc[-168] * 100) if len(close) > 168 else 0
        c30d = ((cp - close.iloc[-720]) / close.iloc[-720] * 100) if len(close) > 720 else 0
        vol = close.iloc[-20:].std() / close.iloc[-20:].mean() * 100
        analysis = {
            'symbol': symbol, 'current_price': round(float(cp), 5), 'trend': trend,
            'change_24h': round(float(c24), 2), 'change_7d': round(float(c7d), 2), 'change_30d': round(float(c30d), 2),
            'rsi': round(float(rsi.iloc[-1]), 2) if not np.isnan(rsi.iloc[-1]) else 50,
            'macd': round(float(macd.iloc[-1]), 5) if not np.isnan(macd.iloc[-1]) else 0,
            'macd_signal': round(float(macd_sig.iloc[-1]), 5) if not np.isnan(macd_sig.iloc[-1]) else 0,
            'macd_histogram': round(float(macd.iloc[-1] - macd_sig.iloc[-1]), 5) if not np.isnan(macd.iloc[-1]) else 0,
            'ema_20': round(float(ema_20.iloc[-1]), 5), 'ema_50': round(float(ema_50.iloc[-1]), 5),
            'ema_200': round(float(ema_200.iloc[-1]), 5) if not np.isnan(ema_200.iloc[-1]) else None,
            'bb_upper': round(float(bb_u.iloc[-1]), 5), 'bb_middle': round(float(bb_m.iloc[-1]), 5),
            'bb_lower': round(float(bb_l.iloc[-1]), 5),
            'atr': round(float(atr.iloc[-1]), 5) if not np.isnan(atr.iloc[-1]) else round(float(cp * 0.01), 5),
            'stochastic': {'k': round(float(stk.iloc[-1]), 2) if not np.isnan(stk.iloc[-1]) else 50,
                           'd': round(float(std.iloc[-1]), 2) if not np.isnan(std.iloc[-1]) else 50},
            'volatility': round(float(vol), 2),
            'support_levels': [round(float(x), 5) for x in sup],
            'resistance_levels': [round(float(x), 5) for x in res],
            'volume_ratio': round(float(vr), 2),
            'volume_trend': "Increasing" if volume.iloc[-1] > volume.iloc[-20:].mean() else "Decreasing",
            'patterns': patterns, 'data_points': len(close), 'timeframe': '6 months hourly data'
        }
        analysis['signals'] = generate_trading_signals(analysis)
        return convert_numpy_types(analysis)
    except Exception as e:
        print(f"Market analysis error: {e}")
        import traceback; traceback.print_exc()
        return None
