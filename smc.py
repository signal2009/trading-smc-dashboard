"""Tab 2: Smart Money Concepts engine (pivots, BOS, CHoCH, sweeps, OB, FVG, premium/discount,
EQH/EQL, trendlines, volume POC, confluence scoring and three strategies)."""
import numpy as np

from config import BOS_LOOKBACK, PIVOT_LENGTH
from data import convert_numpy_types


def calculate_atr_np(df, period=14):
    h = df['High'].values; l = df['Low'].values; c = df['Close'].values
    tr = np.zeros(len(c))
    for i in range(1, len(c)):
        tr[i] = max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1]))
    atr = np.zeros(len(c))
    if len(c) > period:
        atr[period] = np.mean(tr[1:period+1])
        for i in range(period+1, len(c)):
            atr[i] = (atr[i-1]*(period-1)+tr[i])/period
    return atr

def detect_pivots_luxalgo(df, length=PIVOT_LENGTH):
    """Swing highs/lows needing `length` strictly lower/higher bars on BOTH sides.

    Because it looks `length` bars ahead, a pivot is only known `length` bars after it forms (lag).
    """
    highs = df['High'].values; lows = df['Low'].values; opens = df['Open'].values
    closes = df['Close'].values; volume = df['Volume'].values if 'Volume' in df.columns else np.ones(len(df))
    sh_list = []; sl_list = []
    for i in range(length, len(df)-length):
        is_ph = all(highs[i] > highs[i-j] and highs[i] > highs[i+j] for j in range(1, length+1))
        if is_ph:
            bt = max(opens[i], closes[i])
            tc = sum(1 for k in range(i+1, min(i+100, len(df))) if lows[k] < highs[i] and highs[k] > bt)
            zv = sum(volume[k] for k in range(i+1, min(i+100, len(df))) if lows[k] < highs[i] and highs[k] > bt)
            crossed = False; cb = None
            for k in range(i+1, len(df)):
                if closes[k] > highs[i]: crossed = True; cb = k; break
            sh_list.append({'index': i, 'price': float(highs[i]), 'zone_top': float(highs[i]),
                'zone_btm': float(bt), 'touch_count': tc, 'zone_volume': float(zv),
                'crossed': crossed, 'cross_bar': cb, 'type': 'pivot_high'})
        is_pl = all(lows[i] < lows[i-j] and lows[i] < lows[i+j] for j in range(1, length+1))
        if is_pl:
            bb = min(opens[i], closes[i])
            tc = sum(1 for k in range(i+1, min(i+100, len(df))) if lows[k] < bb and highs[k] > lows[i])
            zv = sum(volume[k] for k in range(i+1, min(i+100, len(df))) if lows[k] < bb and highs[k] > lows[i])
            crossed = False; cb = None
            for k in range(i+1, len(df)):
                if closes[k] < lows[i]: crossed = True; cb = k; break
            sl_list.append({'index': i, 'price': float(lows[i]), 'zone_top': float(bb),
                'zone_btm': float(lows[i]), 'touch_count': tc, 'zone_volume': float(zv),
                'crossed': crossed, 'cross_bar': cb, 'type': 'pivot_low'})
    return sh_list, sl_list

def detect_bos(df, swing_highs, swing_lows, atr):
    """Break of structure: a close beyond an unbroken swing level, held >=10 bars and >0.5 ATR past it.

    A BOS is `is_major` when held >=30 bars and the move exceeds 1 ATR.
    """
    close = df['Close'].values; bos = []; bh = set(); bl = set()
    for i in range(len(close)):
        ca = atr[i] if atr[i] > 0 else atr[max(0, i-1)]
        for sh in swing_highs:
            if sh['index'] >= i or sh['index'] in bh: continue
            hd = i - sh['index']
            if hd < 10: continue
            if close[i] > sh['price']:
                ms = close[i] - sh['price']
                if ms > ca * 0.5:
                    bos.append({'index': i, 'direction': 'bullish', 'broken_level': sh['price'],
                        'broken_swing_index': sh['index'], 'hold_duration': hd, 'move_size': float(ms),
                        'atr_ratio': float(ms/ca) if ca > 0 else 0,
                        'is_major': hd >= 30 and ms > ca, 'type': 'bos'})
                    bh.add(sh['index'])
        for sl in swing_lows:
            if sl['index'] >= i or sl['index'] in bl: continue
            hd = i - sl['index']
            if hd < 10: continue
            if close[i] < sl['price']:
                ms = sl['price'] - close[i]
                if ms > ca * 0.5:
                    bos.append({'index': i, 'direction': 'bearish', 'broken_level': sl['price'],
                        'broken_swing_index': sl['index'], 'hold_duration': hd, 'move_size': float(ms),
                        'atr_ratio': float(ms/ca) if ca > 0 else 0,
                        'is_major': hd >= 30 and ms > ca, 'type': 'bos'})
                    bl.add(sl['index'])
    bos.sort(key=lambda x: x['index'])
    return bos

def detect_liquidity_sweeps(df, swing_highs, swing_lows, bos_events):
    h = df['High'].values; l = df['Low'].values; c = df['Close'].values; sweeps = []
    for sl in swing_lows:
        if sl['crossed']: continue
        for i in range(sl['index']+1, min(sl['index']+60, len(df))):
            if l[i] <= sl['zone_top'] and c[i] > sl['zone_top']:
                ds = l[i] < sl['zone_btm']
                cb = any(b['index'] >= i and b['index'] <= i+5 and b['direction'] == 'bullish' for b in bos_events)
                sweeps.append({'index': i, 'type': 'bullish_sweep', 'swept_level': sl['price'],
                    'zone_top': sl['zone_top'], 'zone_btm': sl['zone_btm'], 'swept_swing_index': sl['index'],
                    'deep_sweep': ds, 'caused_bos': cb, 'touch_count': sl['touch_count'], 'zone_volume': sl['zone_volume']})
                break
    for sh in swing_highs:
        if sh['crossed']: continue
        for i in range(sh['index']+1, min(sh['index']+60, len(df))):
            if h[i] >= sh['zone_btm'] and c[i] < sh['zone_btm']:
                ds = h[i] > sh['zone_top']
                cb = any(b['index'] >= i and b['index'] <= i+5 and b['direction'] == 'bearish' for b in bos_events)
                sweeps.append({'index': i, 'type': 'bearish_sweep', 'swept_level': sh['price'],
                    'zone_top': sh['zone_top'], 'zone_btm': sh['zone_btm'], 'swept_swing_index': sh['index'],
                    'deep_sweep': ds, 'caused_bos': cb, 'touch_count': sh['touch_count'], 'zone_volume': sh['zone_volume']})
                break
    return sweeps

def detect_order_blocks(df, bos_events, atr):
    o = df['Open'].values; c = df['Close'].values; h = df['High'].values; l = df['Low'].values
    v = df['Volume'].values if 'Volume' in df.columns else np.ones(len(df)); obs = []
    for bos in bos_events:
        if not bos['is_major']: continue
        bi = bos['index']; d = bos['direction']
        if d == 'bullish':
            for j in range(bi-1, max(bi-15, 0), -1):
                if c[j] < o[j]:
                    ob_body = o[j]-c[j]
                    if ob_body < bos['move_size']*0.8:
                        obs.append({'index': j, 'direction': 'bullish', 'ob_high': float(h[j]), 'ob_low': float(l[j]),
                            'ob_open': float(o[j]), 'ob_close': float(c[j]), 'ob_body': float(ob_body),
                            'bos_index': bi, 'bos_level': bos['broken_level'], 'bos_is_major': True,
                            'bos_move_size': float(bos['move_size']), 'bos_atr_ratio': bos['atr_ratio'],
                            'hold_duration': bos['hold_duration'], 'volume': float(v[j]),
                            'mitigated': False, 'tested': False, 'test_count': 0}); break
        else:
            for j in range(bi-1, max(bi-15, 0), -1):
                if c[j] > o[j]:
                    ob_body = c[j]-o[j]
                    if ob_body < bos['move_size']*0.8:
                        obs.append({'index': j, 'direction': 'bearish', 'ob_high': float(h[j]), 'ob_low': float(l[j]),
                            'ob_open': float(o[j]), 'ob_close': float(c[j]), 'ob_body': float(ob_body),
                            'bos_index': bi, 'bos_level': bos['broken_level'], 'bos_is_major': True,
                            'bos_move_size': float(bos['move_size']), 'bos_atr_ratio': bos['atr_ratio'],
                            'hold_duration': bos['hold_duration'], 'volume': float(v[j]),
                            'mitigated': False, 'tested': False, 'test_count': 0}); break
    return obs

def mark_ob_status(df, order_blocks):
    c = df['Close'].values; h = df['High'].values; l = df['Low'].values
    for ob in order_blocks:
        for i in range(ob['bos_index']+1, len(c)):
            if ob['direction'] == 'bullish':
                if l[i] <= ob['ob_high'] and c[i] >= ob['ob_low']: ob['tested'] = True; ob['test_count'] += 1
                if c[i] < ob['ob_low']*0.998: ob['mitigated'] = True; break
            else:
                if h[i] >= ob['ob_low'] and c[i] <= ob['ob_high']: ob['tested'] = True; ob['test_count'] += 1
                if c[i] > ob['ob_high']*1.002: ob['mitigated'] = True; break
    return order_blocks


# ═══════════════════════════════════════════════════════════════
# NEW: FAIR VALUE GAPS (FVG) — 3-candle imbalance
# Bullish FVG: candle3_low > candle1_high (gap up)
# Bearish FVG: candle3_high < candle1_low (gap down)
# ═══════════════════════════════════════════════════════════════

def detect_fvg(df, atr, min_atr_mult=0.3):
    """Three-candle fair value gaps at least `min_atr_mult` ATR wide, flagged mitigated once price refills them."""
    h = df['High'].values; l = df['Low'].values; c = df['Close'].values; o = df['Open'].values
    v = df['Volume'].values if 'Volume' in df.columns else np.ones(len(df))
    fvgs = []
    for i in range(2, len(df)):
        ca = atr[i] if atr[i] > 0 else 1
        # Bullish FVG: candle i low > candle i-2 high
        if l[i] > h[i-2]:
            gap_size = l[i] - h[i-2]
            if gap_size >= ca * min_atr_mult:
                mid_body = abs(c[i-1] - o[i-1])
                # Check mitigation
                mitigated = False; mit_bar = None
                for k in range(i+1, len(df)):
                    if l[k] <= h[i-2]:  # price filled the gap
                        mitigated = True; mit_bar = k; break
                fvgs.append({
                    'index': i, 'direction': 'bullish', 'top': float(l[i]), 'bottom': float(h[i-2]),
                    'gap_size': float(gap_size), 'atr_ratio': float(gap_size / ca),
                    'impulse_volume': float(v[i-1]), 'mitigated': mitigated, 'mit_bar': mit_bar
                })
        # Bearish FVG: candle i high < candle i-2 low
        if h[i] < l[i-2]:
            gap_size = l[i-2] - h[i]
            if gap_size >= ca * min_atr_mult:
                mitigated = False; mit_bar = None
                for k in range(i+1, len(df)):
                    if h[k] >= l[i-2]:
                        mitigated = True; mit_bar = k; break
                fvgs.append({
                    'index': i, 'direction': 'bearish', 'top': float(l[i-2]), 'bottom': float(h[i]),
                    'gap_size': float(gap_size), 'atr_ratio': float(gap_size / ca),
                    'impulse_volume': float(v[i-1]), 'mitigated': mitigated, 'mit_bar': mit_bar
                })
    return fvgs


# ═══════════════════════════════════════════════════════════════
# NEW: CHANGE OF CHARACTER (CHoCH) — trend reversal signal
# Bullish CHoCH: in bearish structure, price breaks above previous swing high
# Bearish CHoCH: in bullish structure, price breaks below previous swing low
# Different from BOS: CHoCH = FIRST break against the trend (reversal)
# ═══════════════════════════════════════════════════════════════

def detect_choch(df, swing_highs, swing_lows, bos_events):
    """Change of character: the first BOS against the running structure direction."""
    c = df['Close'].values
    choch_events = []
    # Track running structure direction from BOS
    current_dir = None
    last_bos_idx = 0
    for bos in sorted(bos_events, key=lambda x: x['index']):
        bi = bos['index']; bd = bos['direction']
        # CHoCH = first BOS in opposite direction after 2+ in one direction
        if current_dir and bd != current_dir:
            # This is a change of character
            choch_events.append({
                'index': bi,
                'direction': bd,  # new direction
                'from_trend': current_dir,  # old trend
                'broken_level': bos['broken_level'],
                'is_major': bos.get('is_major', False),
                'atr_ratio': bos.get('atr_ratio', 0),
                'type': 'choch'
            })
            current_dir = bd
            last_bos_idx = bi
        elif bd == current_dir or current_dir is None:
            current_dir = bd
            last_bos_idx = bi
    return choch_events


# ═══════════════════════════════════════════════════════════════
# NEW: PREMIUM / DISCOUNT ZONES — Fib 50% of swing range
# Premium = above 50% (sell bias), Discount = below 50% (buy bias)
# Uses most recent significant swing high/low
# ═══════════════════════════════════════════════════════════════

def calculate_premium_discount(df, swing_highs, swing_lows, lookback=200):
    ci = len(df) - 1
    cp = float(df['Close'].iloc[-1])
    si = max(0, ci - lookback)

    recent_highs = [s for s in swing_highs if s['index'] >= si]
    recent_lows = [s for s in swing_lows if s['index'] >= si]

    if not recent_highs or not recent_lows:
        return None

    swing_high = max(s['price'] for s in recent_highs)
    swing_low = min(s['price'] for s in recent_lows)
    swing_range = swing_high - swing_low
    if swing_range <= 0:
        return None

    equilibrium = swing_low + swing_range * 0.5
    # Premium zone: 50-100% (above equilibrium)
    # Discount zone: 0-50% (below equilibrium)
    # OTE zone: 62-79% retracement
    fib_618 = swing_low + swing_range * 0.618
    fib_786 = swing_low + swing_range * 0.786
    fib_382 = swing_low + swing_range * 0.382
    fib_236 = swing_low + swing_range * 0.236

    position_pct = (cp - swing_low) / swing_range * 100 if swing_range > 0 else 50
    zone = 'premium' if cp > equilibrium else 'discount'

    return {
        'swing_high': round(float(swing_high), 5),
        'swing_low': round(float(swing_low), 5),
        'equilibrium': round(float(equilibrium), 5),
        'fib_236': round(float(fib_236), 5),
        'fib_382': round(float(fib_382), 5),
        'fib_618': round(float(fib_618), 5),
        'fib_786': round(float(fib_786), 5),
        'zone': zone,
        'position_pct': round(float(position_pct), 1),
        'ote_top': round(float(fib_786), 5),
        'ote_bottom': round(float(fib_618), 5),
        'in_ote': fib_618 <= cp <= fib_786,
        'in_discount': cp < equilibrium,
        'in_premium': cp > equilibrium
    }


# ═══════════════════════════════════════════════════════════════
# NEW: EQUAL HIGHS / EQUAL LOWS — liquidity clusters
# Multiple swing highs/lows at same level = stop loss cluster = target
# ═══════════════════════════════════════════════════════════════

def detect_equal_levels(swing_highs, swing_lows, range_pct=0.002):
    eqh = []  # equal highs
    eql = []  # equal lows

    # Find clusters of swing highs at similar levels
    for i in range(len(swing_highs)):
        cluster = [swing_highs[i]]
        for j in range(i+1, len(swing_highs)):
            if abs(swing_highs[j]['price'] - swing_highs[i]['price']) / swing_highs[i]['price'] <= range_pct:
                cluster.append(swing_highs[j])
        if len(cluster) >= 2:
            avg_price = sum(s['price'] for s in cluster) / len(cluster)
            already = any(abs(e['level'] - avg_price) / avg_price <= range_pct for e in eqh)
            if not already:
                eqh.append({
                    'level': round(float(avg_price), 5),
                    'count': len(cluster),
                    'bars': [s['index'] for s in cluster],
                    'type': 'equal_high',
                    'swept': any(s['crossed'] for s in cluster)
                })

    for i in range(len(swing_lows)):
        cluster = [swing_lows[i]]
        for j in range(i+1, len(swing_lows)):
            if abs(swing_lows[j]['price'] - swing_lows[i]['price']) / swing_lows[i]['price'] <= range_pct:
                cluster.append(swing_lows[j])
        if len(cluster) >= 2:
            avg_price = sum(s['price'] for s in cluster) / len(cluster)
            already = any(abs(e['level'] - avg_price) / avg_price <= range_pct for e in eql)
            if not already:
                eql.append({
                    'level': round(float(avg_price), 5),
                    'count': len(cluster),
                    'bars': [s['index'] for s in cluster],
                    'type': 'equal_low',
                    'swept': any(s['crossed'] for s in cluster)
                })

    return eqh, eql


# ═══════════════════════════════════════════════════════════════
# NEW: FVG NEAR OB CHECK — confluence factor
# ═══════════════════════════════════════════════════════════════

def fvg_near_ob(fvgs, ob, max_dist=20):
    for fvg in fvgs:
        if fvg['direction'] == ob['direction'] and abs(fvg['index'] - ob['index']) <= max_dist:
            if not fvg['mitigated']:
                return fvg
    return None

def price_in_fvg(cp, fvg, tolerance=0.001):
    tol = abs(fvg['top'] - fvg['bottom']) * 0.3 + fvg['top'] * tolerance
    return (fvg['bottom'] - tol) <= cp <= (fvg['top'] + tol)


def find_protected_levels(df, swing_highs, swing_lows, lookback=300):
    ci = len(df)-1; si = max(0, ci-lookback)
    pl = [s for s in swing_lows if si <= s['index'] <= ci and not s['crossed']]
    ph = [s for s in swing_highs if si <= s['index'] <= ci and not s['crossed']]
    pl.sort(key=lambda x: x['price']); ph.sort(key=lambda x: x['price'], reverse=True)
    return pl, ph


# ═══════════════════════════════════════════════════════════════
# NEW: TRENDLINE DETECTION — Linear regression on swing points
# Finds ascending support trendlines & descending resistance trendlines
# Price touching a trendline near an OB = massive confluence
# ═══════════════════════════════════════════════════════════════

def detect_trendlines(df, swing_highs, swing_lows, atr, lookback=200, min_touches=3):
    ci = len(df) - 1
    si = max(0, ci - lookback)
    cp = float(df['Close'].iloc[-1])
    ca = float(atr[ci]) if atr[ci] > 0 else 1
    trendlines = []

    # --- Ascending support trendline (connect swing lows) ---
    recent_lows = [s for s in swing_lows if s['index'] >= si]
    recent_lows.sort(key=lambda x: x['index'])
    if len(recent_lows) >= 2:
        best_asc = _find_best_trendline(recent_lows, df, atr, 'ascending', ci, ca)
        if best_asc:
            trendlines.append(best_asc)

    # --- Descending resistance trendline (connect swing highs) ---
    recent_highs = [s for s in swing_highs if s['index'] >= si]
    recent_highs.sort(key=lambda x: x['index'])
    if len(recent_highs) >= 2:
        best_desc = _find_best_trendline(recent_highs, df, atr, 'descending', ci, ca)
        if best_desc:
            trendlines.append(best_desc)

    return trendlines


def _find_best_trendline(swings, df, atr, direction, ci, current_atr):
    """Try all pairs of swing points and find the trendline with most touches."""
    h = df['High'].values; l = df['Low'].values; c = df['Close'].values
    cp = float(c[ci])
    best = None
    best_score = 0

    for i in range(len(swings)):
        for j in range(i + 1, len(swings)):
            x1, y1 = swings[i]['index'], swings[i]['price']
            x2, y2 = swings[j]['index'], swings[j]['price']
            if x2 == x1:
                continue

            slope = (y2 - y1) / (x2 - x1)

            # Ascending trendline should have positive slope
            if direction == 'ascending' and slope <= 0:
                continue
            # Descending trendline should have negative slope
            if direction == 'descending' and slope >= 0:
                continue

            # Count touches (swings near the line within 0.5 ATR)
            touches = 0
            touch_bars = []
            for s in swings:
                expected_price = y1 + slope * (s['index'] - x1)
                local_atr = float(atr[s['index']]) if atr[s['index']] > 0 else current_atr
                tolerance = local_atr * 0.5
                if abs(s['price'] - expected_price) <= tolerance:
                    touches += 1
                    touch_bars.append(s['index'])

            if touches < 2:
                continue

            # Check if price hasn't broken through significantly
            broken = False
            for k in range(x2, ci + 1):
                expected = y1 + slope * (k - x1)
                local_atr = float(atr[k]) if atr[k] > 0 else current_atr
                if direction == 'ascending' and c[k] < expected - local_atr * 1.5:
                    broken = True; break
                if direction == 'descending' and c[k] > expected + local_atr * 1.5:
                    broken = True; break

            if broken:
                continue

            # Current projected price on the trendline
            projected = y1 + slope * (ci - x1)
            distance_to_price = abs(cp - projected)
            near_trendline = distance_to_price <= current_atr * 1.5

            score = touches * 10 + (20 if near_trendline else 0) - (ci - x2) * 0.01

            if score > best_score:
                best_score = score
                best = {
                    'type': direction,
                    'start_bar': x1, 'start_price': round(float(y1), 5),
                    'end_bar': x2, 'end_price': round(float(y2), 5),
                    'slope': round(float(slope), 8),
                    'slope_per_bar': round(float(slope), 8),
                    'touches': touches,
                    'touch_bars': touch_bars,
                    'projected_price': round(float(projected), 5),
                    'distance_to_price': round(float(distance_to_price), 5),
                    'distance_atr': round(float(distance_to_price / current_atr), 2) if current_atr > 0 else 999,
                    'near_trendline': near_trendline,
                    'broken': False
                }
    return best


def price_near_trendline(trendlines, cp, direction_match, max_atr_dist=1.5):
    """Check if current price is near a trendline that matches trade direction."""
    for tl in trendlines:
        if not tl['near_trendline']:
            continue
        # Ascending trendline = support = bullish confluence
        if tl['type'] == 'ascending' and direction_match == 'bullish' and tl['distance_atr'] <= max_atr_dist:
            return tl
        # Descending trendline = resistance = bearish confluence
        if tl['type'] == 'descending' and direction_match == 'bearish' and tl['distance_atr'] <= max_atr_dist:
            return tl
    return None


# ═══════════════════════════════════════════════════════════════
# NEW: CONFLUENCE SCORING ENGINE
# Counts how many factors align at a given OB zone
# The more confluences stack, the higher probability
# ═══════════════════════════════════════════════════════════════

def score_confluence(ob, cp, trend, fvgs, choch, pd_zone, eqh, eql,
                     sweeps, trendlines, bos_events, ci):
    """
    Score an OB zone by counting stacked confluences.
    Each confluence adds a point. 5+ = A+ setup.
    Returns (score, list of confluence names, grade).
    """
    score = 0
    factors = []

    # 1. Order Block itself
    if price_in_ob(cp, ob):
        score += 1
        factors.append('Price in OB zone')

    # 2. FVG at OB
    if fvgs:
        nf = fvg_near_ob(fvgs, ob)
        if nf:
            score += 1
            factors.append(f'FVG ({nf["atr_ratio"]:.1f}x ATR)')

    # 3. Premium/Discount alignment
    if pd_zone:
        if ob['direction'] == 'bullish' and pd_zone['in_discount']:
            score += 1
            factors.append(f'Discount zone ({pd_zone["position_pct"]:.0f}%)')
        elif ob['direction'] == 'bearish' and pd_zone['in_premium']:
            score += 1
            factors.append(f'Premium zone ({pd_zone["position_pct"]:.0f}%)')
        if pd_zone.get('in_ote'):
            score += 1
            factors.append('OTE (61.8-78.6%)')

    # 4. Liquidity sweep near OB
    if sweeps:
        st = 'bullish_sweep' if ob['direction'] == 'bullish' else 'bearish_sweep'
        for sw in sweeps:
            if sw['type'] == st and abs(sw['index'] - ob['index']) < 50:
                score += 1
                factors.append('Liquidity sweep')
                if sw.get('deep_sweep'):
                    score += 1
                    factors.append('Deep sweep')
                break

    # 5. CHoCH confirmation
    if choch:
        for ch in choch:
            if ch['direction'] == ob['direction'] and abs(ch['index'] - ob['bos_index']) <= 30:
                score += 1
                factors.append('CHoCH confirmed')
                break

    # 6. Trendline touch
    if trendlines:
        tl = price_near_trendline(trendlines, cp, ob['direction'])
        if tl:
            score += 1
            factors.append(f'Trendline ({tl["type"]}, {tl["touches"]}T)')

    # 7. Equal levels nearby (liquidity cluster)
    if ob['direction'] == 'bullish' and eql:
        for eq in eql:
            if abs(eq['level'] - ob['ob_low']) / max(ob['ob_low'], 0.0001) < 0.005 and not eq['swept']:
                score += 1
                factors.append(f'EQL cluster ×{eq["count"]}')
                break
    elif ob['direction'] == 'bearish' and eqh:
        for eq in eqh:
            if abs(eq['level'] - ob['ob_high']) / max(ob['ob_high'], 0.0001) < 0.005 and not eq['swept']:
                score += 1
                factors.append(f'EQH cluster ×{eq["count"]}')
                break

    # 8. Impulsive BOS move
    if ob.get('bos_atr_ratio', 0) > 1.5:
        score += 1
        factors.append(f'Impulsive BOS ({ob["bos_atr_ratio"]:.1f}x ATR)')

    # Grade
    if score >= 7:
        grade = 'A+'
    elif score >= 5:
        grade = 'A'
    elif score >= 4:
        grade = 'B+'
    elif score >= 3:
        grade = 'B'
    elif score >= 2:
        grade = 'C'
    else:
        grade = 'D'

    return score, factors, grade


# ═══════════════════════════════════════════════════════════════
# NEW: WEIGHTED VOLUME POC (Point of Control)
# Inspired by Flux Charts WVPPP — finds the price level with
# highest weighted volume between swing range.
# POC = institutional fair value = price magnet
# ═══════════════════════════════════════════════════════════════

def calculate_weighted_volume_poc(df, swing_highs, swing_lows, atr, row_count=30, lookback=200, weight_mode='recent'):
    ci = len(df) - 1
    si = max(0, ci - lookback)
    cp = float(df['Close'].iloc[-1])
    h = df['High'].values; l = df['Low'].values; c = df['Close'].values; o = df['Open'].values
    v = df['Volume'].values if 'Volume' in df.columns else np.ones(len(df))
    ca = float(atr[ci]) if atr[ci] > 0 else 1

    recent_highs = [s for s in swing_highs if s['index'] >= si]
    recent_lows = [s for s in swing_lows if s['index'] >= si]
    if not recent_highs or not recent_lows:
        return None

    range_top = max(s['price'] for s in recent_highs)
    range_bottom = min(s['price'] for s in recent_lows)
    total_range = range_top - range_bottom
    if total_range <= 0:
        return None

    step = total_range / row_count
    rows = []
    for r in range(row_count):
        row_top = range_top - step * r
        row_bottom = row_top - step
        rows.append({'top': row_top, 'bottom': row_bottom, 'bull_vol': 0.0, 'bear_vol': 0.0, 'total_vol': 0.0})

    # Fill volume into rows with weighting
    bars_analyzed = min(lookback, ci - si)
    for i in range(si, ci + 1):
        vol = float(v[i])
        dist = ci - i  # distance from current bar

        # Weight by recency (Flux Charts approach)
        if weight_mode == 'recent':
            weight = 0.85 / max(dist + 1, 1) + 0.15
        elif weight_mode == 'past':
            weight = 0.85 * ((dist + 1) / max(bars_analyzed, 1)) + 0.15
        else:
            weight = 1.0

        weighted_vol = vol * weight
        bar_high = float(h[i])
        bar_low = float(l[i])
        is_bull = c[i] > o[i]

        for row in rows:
            # Check if bar intersects this row
            if bar_low <= row['top'] and bar_high >= row['bottom']:
                if is_bull:
                    row['bull_vol'] += weighted_vol
                else:
                    row['bear_vol'] += weighted_vol
                row['total_vol'] += weighted_vol

    # Find POC (row with max volume)
    max_vol = 0
    poc_row = None
    for row in rows:
        if row['total_vol'] > max_vol:
            max_vol = row['total_vol']
            poc_row = row

    if poc_row is None or max_vol == 0:
        return None

    poc_price = (poc_row['top'] + poc_row['bottom']) / 2
    poc_bull_pct = (poc_row['bull_vol'] / poc_row['total_vol'] * 100) if poc_row['total_vol'] > 0 else 50

    # Value Area (70% of total volume around POC)
    total_volume_all = sum(r['total_vol'] for r in rows)
    va_target = total_volume_all * 0.70
    poc_idx = rows.index(poc_row)
    va_vol = poc_row['total_vol']
    va_high_idx = poc_idx
    va_low_idx = poc_idx

    while va_vol < va_target and (va_high_idx > 0 or va_low_idx < len(rows) - 1):
        up_vol = rows[va_high_idx - 1]['total_vol'] if va_high_idx > 0 else 0
        down_vol = rows[va_low_idx + 1]['total_vol'] if va_low_idx < len(rows) - 1 else 0
        if up_vol >= down_vol and va_high_idx > 0:
            va_high_idx -= 1
            va_vol += up_vol
        elif va_low_idx < len(rows) - 1:
            va_low_idx += 1
            va_vol += down_vol
        else:
            break

    vah = rows[va_high_idx]['top']
    val = rows[va_low_idx]['bottom']

    # Price position relative to POC
    above_poc = cp > poc_price
    distance_to_poc = abs(cp - poc_price)
    poc_atr_dist = distance_to_poc / ca if ca > 0 else 0

    return {
        'poc_price': round(float(poc_price), 5),
        'poc_bull_pct': round(float(poc_bull_pct), 1),
        'poc_bear_pct': round(float(100 - poc_bull_pct), 1),
        'vah': round(float(vah), 5),  # value area high
        'val': round(float(val), 5),  # value area low
        'above_poc': above_poc,
        'distance_to_poc': round(float(distance_to_poc), 5),
        'poc_atr_dist': round(float(poc_atr_dist), 2),
        'price_in_value_area': val <= cp <= vah,
        'range_top': round(float(range_top), 5),
        'range_bottom': round(float(range_bottom), 5),
        'total_volume': round(float(total_volume_all), 0),
        'poc_volume': round(float(max_vol), 0)
    }


# ═══════════════════════════════════════════════════════════════
# NEW: DIRECTION CONFIRMATION ENGINE
# Reads ALL current signals and gives a clear directional verdict
# Answers: "Where is the market moving RIGHT NOW?"
# ═══════════════════════════════════════════════════════════════

def confirm_direction(df, bos_events, choch_events, fvgs, pd_zone, trendlines,
                      sweeps, eqh, eql, poc_data, atr, swing_highs, swing_lows):
    """
    Multi-factor directional confirmation.
    Each factor votes BULL (+) or BEAR (-).
    Final verdict based on weighted consensus.
    """
    ci = len(df) - 1
    cp = float(df['Close'].iloc[-1])
    c = df['Close'].values; h = df['High'].values; l = df['Low'].values; o = df['Open'].values
    v = df['Volume'].values if 'Volume' in df.columns else np.ones(len(df))
    ca = float(atr[ci]) if atr[ci] > 0 else 1

    votes = []  # (weight, direction_score, factor_name)
    # direction_score: +1 = bullish, -1 = bearish, 0 = neutral

    # ── 1. BOS TREND (weight: 3) — most reliable structural signal ──
    recent_bos = [b for b in bos_events if ci - 150 <= b['index'] <= ci]
    bull_bos = sum(1 for b in recent_bos if b['direction'] == 'bullish')
    bear_bos = sum(1 for b in recent_bos if b['direction'] == 'bearish')
    if bull_bos > bear_bos:
        votes.append((3, 1, f'BOS trend: {bull_bos} bull vs {bear_bos} bear'))
    elif bear_bos > bull_bos:
        votes.append((3, -1, f'BOS trend: {bear_bos} bear vs {bull_bos} bull'))
    else:
        votes.append((1, 0, 'BOS trend: neutral'))

    # ── 2. LATEST BOS DIRECTION (weight: 2) — momentum ──
    if recent_bos:
        last_bos = recent_bos[-1]
        w = 2
        if last_bos.get('is_major'):
            w = 3
        d = 1 if last_bos['direction'] == 'bullish' else -1
        votes.append((w, d, f'Last BOS: {last_bos["direction"]} ({"major" if last_bos.get("is_major") else "minor"})'))

    # ── 3. CHoCH — recent reversal signal (weight: 3) ──
    if choch_events:
        recent_ch = [ch for ch in choch_events if ci - 100 <= ch['index'] <= ci]
        if recent_ch:
            latest_ch = recent_ch[-1]
            d = 1 if latest_ch['direction'] == 'bullish' else -1
            w = 3 if latest_ch.get('is_major') else 2
            votes.append((w, d, f'CHoCH: {latest_ch["from_trend"]}→{latest_ch["direction"]}'))

    # ── 4. PRICE MOMENTUM — last N candles (weight: 2) ──
    if ci >= 10:
        mom_5 = cp - c[ci - 5]
        mom_10 = cp - c[ci - 10]
        mom_20 = cp - c[ci - 20] if ci >= 20 else 0
        total_mom = mom_5 + mom_10 * 0.5 + mom_20 * 0.25
        if total_mom > ca * 0.5:
            votes.append((2, 1, f'Momentum: bullish ({mom_5/ca:.1f}x ATR 5-bar)'))
        elif total_mom < -ca * 0.5:
            votes.append((2, -1, f'Momentum: bearish ({mom_5/ca:.1f}x ATR 5-bar)'))
        else:
            votes.append((1, 0, 'Momentum: flat'))

    # ── 5. HIGHER HIGHS / LOWER LOWS (weight: 2) ──
    if len(swing_highs) >= 2 and len(swing_lows) >= 2:
        last_2h = sorted(swing_highs[-3:], key=lambda x: x['index'])
        last_2l = sorted(swing_lows[-3:], key=lambda x: x['index'])
        hh = last_2h[-1]['price'] > last_2h[-2]['price'] if len(last_2h) >= 2 else False
        hl = last_2l[-1]['price'] > last_2l[-2]['price'] if len(last_2l) >= 2 else False
        ll = last_2l[-1]['price'] < last_2l[-2]['price'] if len(last_2l) >= 2 else False
        lh = last_2h[-1]['price'] < last_2h[-2]['price'] if len(last_2h) >= 2 else False
        if hh and hl:
            votes.append((2, 1, 'Structure: HH + HL (uptrend)'))
        elif ll and lh:
            votes.append((2, -1, 'Structure: LL + LH (downtrend)'))
        elif hh:
            votes.append((1, 1, 'Structure: higher highs'))
        elif ll:
            votes.append((1, -1, 'Structure: lower lows'))

    # ── 6. FVG BIAS — unmitigated FVGs direction (weight: 1) ──
    if fvgs:
        recent_fvg = [f for f in fvgs if not f['mitigated'] and ci - f['index'] <= 100]
        bull_fvg = sum(1 for f in recent_fvg if f['direction'] == 'bullish')
        bear_fvg = sum(1 for f in recent_fvg if f['direction'] == 'bearish')
        if bull_fvg > bear_fvg:
            votes.append((1, 1, f'FVG bias: {bull_fvg} bull gaps'))
        elif bear_fvg > bull_fvg:
            votes.append((1, -1, f'FVG bias: {bear_fvg} bear gaps'))

    # ── 7. PREMIUM/DISCOUNT ZONE (weight: 2) ──
    if pd_zone:
        if pd_zone['in_discount']:
            votes.append((2, 1, f'Discount zone ({pd_zone["position_pct"]:.0f}%) — buy territory'))
        elif pd_zone['in_premium']:
            votes.append((2, -1, f'Premium zone ({pd_zone["position_pct"]:.0f}%) — sell territory'))
        if pd_zone.get('in_ote'):
            votes.append((1, 0, 'Inside OTE — reversal zone'))

    # ── 8. TRENDLINE POSITION (weight: 2) ──
    if trendlines:
        for tl in trendlines:
            if tl['type'] == 'ascending' and tl['near_trendline']:
                votes.append((2, 1, f'At ascending trendline support ({tl["touches"]}T)'))
            elif tl['type'] == 'descending' and tl['near_trendline']:
                votes.append((2, -1, f'At descending trendline resistance ({tl["touches"]}T)'))
            elif tl['type'] == 'ascending' and cp > tl['projected_price']:
                votes.append((1, 1, 'Above ascending trendline'))
            elif tl['type'] == 'descending' and cp < tl['projected_price']:
                votes.append((1, -1, 'Below descending trendline'))

    # ── 9. POC POSITION (weight: 2) ──
    if poc_data:
        if poc_data['above_poc'] and poc_data['poc_atr_dist'] > 0.5:
            votes.append((2, 1, f'Above POC ${poc_data["poc_price"]} ({poc_data["poc_atr_dist"]}x ATR)'))
        elif not poc_data['above_poc'] and poc_data['poc_atr_dist'] > 0.5:
            votes.append((2, -1, f'Below POC ${poc_data["poc_price"]} ({poc_data["poc_atr_dist"]}x ATR)'))
        else:
            votes.append((1, 0, f'At POC ${poc_data["poc_price"]} — equilibrium'))
        # POC volume bias
        if poc_data['poc_bull_pct'] > 60:
            votes.append((1, 1, f'POC volume: {poc_data["poc_bull_pct"]:.0f}% buyers'))
        elif poc_data['poc_bear_pct'] > 60:
            votes.append((1, -1, f'POC volume: {poc_data["poc_bear_pct"]:.0f}% sellers'))

    # ── 10. RECENT SWEEPS (weight: 2) ──
    if sweeps:
        recent_sw = [s for s in sweeps if ci - s['index'] <= 50]
        bull_sw = sum(1 for s in recent_sw if s['type'] == 'bullish_sweep')
        bear_sw = sum(1 for s in recent_sw if s['type'] == 'bearish_sweep')
        if bull_sw > 0 and any(s.get('caused_bos') for s in recent_sw if s['type'] == 'bullish_sweep'):
            votes.append((2, 1, f'Bullish sweep → BOS (reversal up)'))
        elif bear_sw > 0 and any(s.get('caused_bos') for s in recent_sw if s['type'] == 'bearish_sweep'):
            votes.append((2, -1, f'Bearish sweep → BOS (reversal down)'))

    # ── 11. VOLUME TREND (weight: 1) ──
    if ci >= 20:
        avg_vol_20 = np.mean(v[ci-20:ci])
        avg_vol_5 = np.mean(v[ci-5:ci])
        last_candle_bull = c[ci] > o[ci]
        if avg_vol_5 > avg_vol_20 * 1.3:
            d = 1 if last_candle_bull else -1
            votes.append((1, d, f'Rising volume on {"bullish" if last_candle_bull else "bearish"} candles'))

    # ── 12. CANDLE STRUCTURE — last 3 bars (weight: 1) ──
    if ci >= 3:
        bull_candles = sum(1 for k in range(ci - 2, ci + 1) if c[k] > o[k])
        bear_candles = 3 - bull_candles
        if bull_candles == 3:
            votes.append((1, 1, '3 consecutive bullish candles'))
        elif bear_candles == 3:
            votes.append((1, -1, '3 consecutive bearish candles'))

    # ── 13. EQH/EQL TARGETS (weight: 1) — where liquidity sits ──
    if eqh:
        unswept_eqh = [e for e in eqh if not e['swept']]
        if unswept_eqh:
            nearest = min(unswept_eqh, key=lambda e: abs(e['level'] - cp))
            if nearest['level'] > cp:
                votes.append((1, 1, f'EQH target above ${nearest["level"]} (liquidity magnet)'))
    if eql:
        unswept_eql = [e for e in eql if not e['swept']]
        if unswept_eql:
            nearest = min(unswept_eql, key=lambda e: abs(e['level'] - cp))
            if nearest['level'] < cp:
                votes.append((1, -1, f'EQL target below ${nearest["level"]} (liquidity magnet)'))

    # ── TALLY VOTES ──
    total_weight = sum(w for w, _, _ in votes) if votes else 1
    weighted_sum = sum(w * d for w, d, _ in votes)
    max_possible = sum(w for w, _, _ in votes)

    # Normalize to -100 to +100
    if max_possible > 0:
        direction_score = (weighted_sum / max_possible) * 100
    else:
        direction_score = 0

    # Build factors lists
    bull_factors = [name for w, d, name in votes if d > 0]
    bear_factors = [name for w, d, name in votes if d < 0]
    neutral_factors = [name for w, d, name in votes if d == 0]

    # Verdict
    if direction_score >= 60:
        verdict = 'STRONG BULLISH'
        emoji = '🟢🟢'
    elif direction_score >= 30:
        verdict = 'BULLISH'
        emoji = '🟢'
    elif direction_score >= 10:
        verdict = 'LEAN BULLISH'
        emoji = '🟢⚪'
    elif direction_score <= -60:
        verdict = 'STRONG BEARISH'
        emoji = '🔴🔴'
    elif direction_score <= -30:
        verdict = 'BEARISH'
        emoji = '🔴'
    elif direction_score <= -10:
        verdict = 'LEAN BEARISH'
        emoji = '🔴⚪'
    else:
        verdict = 'NEUTRAL'
        emoji = '⚪'

    return {
        'verdict': verdict,
        'direction_score': round(float(direction_score), 1),
        'bull_count': len(bull_factors),
        'bear_count': len(bear_factors),
        'neutral_count': len(neutral_factors),
        'bull_factors': bull_factors,
        'bear_factors': bear_factors,
        'neutral_factors': neutral_factors,
        'total_factors': len(votes),
        'confidence': round(abs(float(direction_score)), 1)
    }



def get_bos_trend(bos_events, lookback, ci):
    recent = [b for b in bos_events if ci-lookback <= b['index'] <= ci]
    bc = sum(1 for b in recent if b['direction'] == 'bullish')
    sc = sum(1 for b in recent if b['direction'] == 'bearish')
    if bc > sc and bc >= 2: return 'bullish', bc, sc, recent
    elif sc > bc and sc >= 2: return 'bearish', bc, sc, recent
    return 'neutral', bc, sc, recent

def check_retracement_bos(bos_events, td, ci, lookback=200):
    recent = [b for b in bos_events if ci-lookback <= b['index'] <= ci]
    if td == 'bullish':
        for br in reversed([b for b in recent if b['direction'] == 'bearish']):
            ba = [b for b in recent if b['direction'] == 'bullish' and b['index'] > br['index']]
            if ba: return True, br, ba[-1]
    elif td == 'bearish':
        for br in reversed([b for b in recent if b['direction'] == 'bullish']):
            ba = [b for b in recent if b['direction'] == 'bearish' and b['index'] > br['index']]
            if ba: return True, br, ba[-1]
    return False, None, None

def detect_trend_then_reversal(bos_events, ci):
    recent = [b for b in bos_events if b['index'] <= ci]
    if len(recent) < 3: return None, None, None
    for i in range(len(recent)-1, 1, -1):
        cb = recent[i]; od = 'bearish' if cb['direction'] == 'bullish' else 'bullish'
        con = 0
        for j in range(i-1, max(i-20, -1), -1):
            if j < 0: break
            if recent[j]['direction'] == od: con += 1
            elif con >= 2: break
            else: con = 0
        if con >= 2: return cb, od, None
    return None, None, None

def price_in_ob(cp, ob, tolerance=0.003):
    zr = ob['ob_high'] - ob['ob_low']; tol = max(zr*0.5, ob['ob_high']*tolerance)
    return (ob['ob_low']-tol) <= cp <= (ob['ob_high']+tol)

def build_signal(sn, name, direction, stype, conf, cp, ob, sl, factors):
    risk = abs(cp - sl)
    if risk <= 0: return None
    if direction == 'BUY': t1,t2,t3 = cp+risk*2, cp+risk*3, cp+risk*5
    else: t1,t2,t3 = cp-risk*2, cp-risk*3, cp-risk*5
    return {'strategy': f'Strategy {sn}', 'strategy_name': name, 'direction': direction,
        'signal_type': stype, 'confidence': min(conf, 95), 'entry_price': round(cp, 5),
        'entry_zone': f'{round(ob["ob_low"], 5)} — {round(ob["ob_high"], 5)}',
        'stop_loss': round(sl, 5), 'take_profit_1': round(t1, 5), 'take_profit_2': round(t2, 5),
        'take_profit_3': round(t3, 5), 'risk_reward': '1:2 / 1:3 / 1:5',
        'risk_pct': round(risk/cp*100, 3) if cp > 0 else 0,
        'ob_origin_bar': ob['index'], 'ob_bos_bar': ob['bos_index'],
        'ob_atr_ratio': round(ob.get('bos_atr_ratio', 0), 2),
        'ob_hold_bars': ob.get('hold_duration', 0), 'factors': factors}

def strategy_1(df, sh, sl, bos, sweeps, obs, pl, ph, fvgs=None, choch=None, pd_zone=None, eqh=None, eql=None, trendlines=None):
    signals = []; ci = len(df)-1; cp = float(df['Close'].iloc[-1])
    trend, bc, sc, _ = get_bos_trend(bos, BOS_LOOKBACK, ci)
    if trend == 'neutral': return signals
    hrb, _, _ = check_retracement_bos(bos, trend, ci, 200)
    st = 'bullish_sweep' if trend == 'bullish' else 'bearish_sweep'
    vobs = [o for o in obs if o['direction']==trend and ci-BOS_LOOKBACK<=o['index']<=ci and not o['mitigated']]
    for ob in vobs:
        if not price_in_ob(cp, ob): continue
        ov = False; ss = 'none'; bsw = None
        for sw in sweeps:
            if sw['type'] != st: continue
            d = abs(sw['index'] - ob['index'])
            if d < 50: ov = True; ss = 'strong' if sw['deep_sweep'] or d < 15 else 'moderate'; bsw = sw; break
        if trend == 'bullish': slp = (pl[0]['price']*0.998) if pl else ob['ob_low']*0.998
        else: slp = (ph[0]['price']*1.002) if ph else ob['ob_high']*1.002
        conf = 40
        if ov: conf += 25
        if ss == 'strong': conf += 10
        if hrb: conf += 15
        if (bc if trend=='bullish' else sc) >= 3: conf += 5
        if ob.get('bos_atr_ratio', 0) > 1.5: conf += 5
        if bsw and bsw.get('caused_bos'): conf += 5
        nearby_fvg = fvg_near_ob(fvgs, ob) if fvgs else None
        if nearby_fvg: conf += 10
        if pd_zone:
            if trend == 'bullish' and pd_zone['in_discount']: conf += 10
            elif trend == 'bearish' and pd_zone['in_premium']: conf += 10
            if pd_zone.get('in_ote'): conf += 5
        if trend == 'bullish' and eql:
            for eq in eql:
                if abs(eq['level'] - ob['ob_low']) / max(ob['ob_low'], 0.0001) < 0.005 and not eq['swept']:
                    conf += 5; break
        elif trend == 'bearish' and eqh:
            for eq in eqh:
                if abs(eq['level'] - ob['ob_high']) / max(ob['ob_high'], 0.0001) < 0.005 and not eq['swept']:
                    conf += 5; break
        # TRENDLINE confluence
        tl_match = price_near_trendline(trendlines, cp, trend) if trendlines else None
        if tl_match: conf += 10
        if conf < 55: continue
        # CONFLUENCE SCORE
        cscore, cfactors, cgrade = score_confluence(ob, cp, trend, fvgs, choch, pd_zone, eqh, eql, sweeps, trendlines or [], bos, ci)
        cnt = bc if trend=='bullish' else sc
        f = [f'[{cgrade}] {cscore} confluences stacked']
        f.append(f'{cnt} {trend} BOS (major)')
        if ov: f.append(f'Liquidity swept ({ss})')
        if hrb: f.append('Retracement broke structure')
        if nearby_fvg: f.append(f'FVG confluence ({nearby_fvg["atr_ratio"]:.1f}x ATR gap)')
        if tl_match: f.append(f'Trendline touch ({tl_match["type"]}, {tl_match["touches"]} touches)')
        if pd_zone:
            f.append(f'Price in {pd_zone["zone"].upper()} zone ({pd_zone["position_pct"]:.0f}%)')
            if pd_zone.get('in_ote'): f.append('Inside OTE (61.8-78.6%) — optimal entry')
        f.append(f'BOS {ob.get("bos_atr_ratio",0):.1f}x ATR | held {ob.get("hold_duration",0)} bars')
        dr = 'BUY' if trend=='bullish' else 'SELL'
        sig = build_signal(1, 'BOS+Liquidity+OB', dr, 'Trend Continuation', conf, cp, ob, slp, f)
        if sig:
            sig['ob_validated']=ov; sig['sweep_strength']=ss; sig['retracement_broke_structure']=hrb
            sig['fvg_confluence']=nearby_fvg is not None; sig['trendline']=tl_match is not None
            sig['confluence_score']=cscore; sig['confluence_grade']=cgrade
            signals.append(sig)
    return signals

def strategy_2(df, sh, sl, bos, obs, pl, ph, fvgs=None, choch=None, pd_zone=None, trendlines=None, eqh=None, eql=None, sweeps=None):
    signals = []; ci = len(df)-1; cp = float(df['Close'].iloc[-1])
    rb, pt, _ = detect_trend_then_reversal(bos, ci)
    if rb is None: return signals
    rd = rb['direction']; ri = rb['index']
    hrb, _, _ = check_retracement_bos(bos, rd, ci, 300)
    choch_confirmed = False
    if choch:
        for ch in choch:
            if ch['direction'] == rd and abs(ch['index'] - ri) <= 30:
                choch_confirmed = True; break
    si_r = max(0, ci-BOS_LOOKBACK)
    vobs = [o for o in obs if o['direction']==rd and si_r<=o['index']<=ci and not o['mitigated']]
    if not vobs: return signals
    vobs.sort(key=lambda x: x['index'])
    for tob in vobs[:3]:
        if not price_in_ob(cp, tob): continue
        od = ci-tob['index']
        if rd=='bullish': slp = (pl[0]['price']*0.998) if pl else tob['ob_low']*0.998
        else: slp = (ph[0]['price']*1.002) if ph else tob['ob_high']*1.002
        conf = 55
        if hrb: conf += 15
        if rb.get('is_major'): conf += 10
        if od > 100: conf += 5
        if tob.get('bos_atr_ratio', 0) > 1.5: conf += 5
        if choch_confirmed: conf += 10
        nearby_fvg = fvg_near_ob(fvgs, tob) if fvgs else None
        if nearby_fvg: conf += 10
        if pd_zone:
            if rd == 'bullish' and pd_zone['in_discount']: conf += 10
            elif rd == 'bearish' and pd_zone['in_premium']: conf += 10
        tl_match = price_near_trendline(trendlines, cp, rd) if trendlines else None
        if tl_match: conf += 10
        if conf < 55: continue
        cscore, cfactors, cgrade = score_confluence(tob, cp, rd, fvgs, choch, pd_zone, eqh, eql, sweeps or [], trendlines or [], bos, ci)
        f = [f'[{cgrade}] {cscore} confluences stacked']
        f.append(f'Was {pt} → reversed {rd}')
        if choch_confirmed: f.append('CHoCH confirmed — character changed')
        if hrb: f.append('Retracement broke structure')
        if nearby_fvg: f.append(f'FVG at OB ({nearby_fvg["atr_ratio"]:.1f}x ATR)')
        if tl_match: f.append(f'Trendline touch ({tl_match["type"]}, {tl_match["touches"]} touches)')
        if pd_zone: f.append(f'{pd_zone["zone"].upper()} zone ({pd_zone["position_pct"]:.0f}%)')
        f.append(f'OB {od} bars back | {tob.get("bos_atr_ratio",0):.1f}x ATR')
        dr = 'BUY' if rd=='bullish' else 'SELL'
        sig = build_signal(2, 'Structure Break+OB', dr, 'Structure Break', conf, cp, tob, slp, f)
        if sig:
            sig['retracement_broke_structure']=hrb; sig['ob_distance_bars']=od; sig['choch_confirmed']=choch_confirmed
            sig['confluence_score']=cscore; sig['confluence_grade']=cgrade
            signals.append(sig)
    return signals

def strategy_3(df, sh, sl, bos, obs, pl, ph, fvgs=None, pd_zone=None):
    signals = []; ci = len(df)-1; cp = float(df['Close'].iloc[-1])
    tobs = [o for o in obs if o['tested'] and not o['mitigated'] and o['test_count'] >= 1]
    if not tobs: return signals
    for ob in tobs:
        od = 'bearish' if ob['direction']=='bullish' else 'bullish'
        baf = [b for b in bos if b['index']>ob['bos_index'] and b['direction']==od]
        if not baf: continue
        lob = baf[-1]
        bbk = [b for b in bos if b['index']>lob['index'] and b['direction']==ob['direction']]
        if not bbk: continue
        hrb, _, _ = check_retracement_bos(bos, ob['direction'], ci, 300)
        if not price_in_ob(cp, ob, 0.005): continue
        if ob['direction']=='bullish':
            rl = [p for p in pl if p['index']>lob['index']]
            slp = (rl[0]['price']*0.998) if rl else (pl[0]['price']*0.998 if pl else ob['ob_low']*0.998)
        else:
            rh = [p for p in ph if p['index']>lob['index']]
            slp = (rh[0]['price']*1.002) if rh else (ph[0]['price']*1.002 if ph else ob['ob_high']*1.002)
        conf = 50
        if hrb: conf += 15
        if ob['test_count'] == 1: conf += 10
        elif ob['test_count'] <= 3: conf += 5
        if len(bbk) >= 2: conf += 10
        if any(b.get('is_major') for b in bbk): conf += 10
        # NEW: FVG confluence
        nearby_fvg = fvg_near_ob(fvgs, ob) if fvgs else None
        if nearby_fvg: conf += 10
        # NEW: Premium/Discount
        if pd_zone:
            if ob['direction'] == 'bullish' and pd_zone['in_discount']: conf += 5
            elif ob['direction'] == 'bearish' and pd_zone['in_premium']: conf += 5
        if conf < 55: continue
        f = [f'OB tested {ob["test_count"]}x', f'Market reversed ({len(baf)} {od} BOS)',
             f'Structure back ({len(bbk)} {ob["direction"]} BOS)']
        if hrb: f.append('Retracement broke structure')
        if nearby_fvg: f.append(f'FVG at OB ({nearby_fvg["atr_ratio"]:.1f}x ATR)')
        if pd_zone: f.append(f'{pd_zone["zone"].upper()} zone ({pd_zone["position_pct"]:.0f}%)')
        f.append('Re-entry — expecting mitigation')
        dr = 'BUY' if ob['direction']=='bullish' else 'SELL'
        sig = build_signal(3, 'Recovery Re-entry', dr, 'Recovery', conf, cp, ob, slp, f)
        if sig: sig['ob_test_count']=ob['test_count']; sig['retracement_broke_structure']=hrb; signals.append(sig)
    return signals

def analyze_smc(df, symbol):
    """Run the full SMC pipeline on an OHLCV frame (needs >=100 bars) and return a JSON-safe dict, or None."""
    if df is None or df.empty or len(df) < 100: return None
    try:
        cp = float(df['Close'].iloc[-1]); ci = len(df)-1
        atr = calculate_atr_np(df, 14)
        swing_highs, swing_lows = detect_pivots_luxalgo(df, PIVOT_LENGTH)
        if not swing_highs or not swing_lows: return {'symbol': symbol, 'error': 'Not enough pivots'}
        bos_events = detect_bos(df, swing_highs, swing_lows, atr)
        sweeps = detect_liquidity_sweeps(df, swing_highs, swing_lows, bos_events)
        order_blocks = detect_order_blocks(df, bos_events, atr)
        order_blocks = mark_ob_status(df, order_blocks)
        protected_lows, protected_highs = find_protected_levels(df, swing_highs, swing_lows, BOS_LOOKBACK)
        trend, bc, sc, _ = get_bos_trend(bos_events, BOS_LOOKBACK, ci)

        # NEW DETECTIONS (wrapped — won't crash if one fails)
        try:
            fvgs = detect_fvg(df, atr)
        except Exception as e:
            print(f"FVG error: {e}"); fvgs = []
        try:
            choch_events = detect_choch(df, swing_highs, swing_lows, bos_events)
        except Exception as e:
            print(f"CHoCH error: {e}"); choch_events = []
        try:
            pd_zone = calculate_premium_discount(df, swing_highs, swing_lows)
        except Exception as e:
            print(f"P/D error: {e}"); pd_zone = None
        try:
            eqh, eql = detect_equal_levels(swing_highs, swing_lows)
        except Exception as e:
            print(f"EQ error: {e}"); eqh, eql = [], []
        try:
            trendlines = detect_trendlines(df, swing_highs, swing_lows, atr)
        except Exception as e:
            print(f"Trendline error: {e}"); trendlines = []
        try:
            poc_data = calculate_weighted_volume_poc(df, swing_highs, swing_lows, atr)
        except Exception as e:
            print(f"POC error: {e}"); poc_data = None
        try:
            direction = confirm_direction(df, bos_events, choch_events, fvgs, pd_zone,
                                           trendlines, sweeps, eqh, eql, poc_data, atr,
                                           swing_highs, swing_lows)
        except Exception as e:
            print(f"Direction error: {e}"); direction = None

        # Pass ALL data to strategies
        s1 = strategy_1(df, swing_highs, swing_lows, bos_events, sweeps, order_blocks,
                         protected_lows, protected_highs, fvgs, choch_events, pd_zone, eqh, eql, trendlines)
        s2 = strategy_2(df, swing_highs, swing_lows, bos_events, order_blocks,
                         protected_lows, protected_highs, fvgs, choch_events, pd_zone, trendlines, eqh, eql, sweeps)
        s3 = strategy_3(df, swing_highs, swing_lows, bos_events, order_blocks,
                         protected_lows, protected_highs, fvgs, pd_zone)

        all_signals = s1+s2+s3; all_signals.sort(key=lambda x: x['confidence'], reverse=True)
        active_obs = [{'bar': ob['index'], 'direction': ob['direction'],
            'zone': f'{round(ob["ob_low"],5)} — {round(ob["ob_high"],5)}', 'bos_bar': ob['bos_index'],
            'tested': ob['tested'], 'test_count': ob['test_count'],
            'atr_ratio': round(ob.get('bos_atr_ratio',0),2), 'hold_bars': ob.get('hold_duration',0)}
            for ob in order_blocks if not ob['mitigated'] and ci-ob['index'] <= BOS_LOOKBACK]
        liq_zones = []
        for sh in swing_highs[-10:]:
            if not sh['crossed'] and ci-sh['index'] <= BOS_LOOKBACK:
                liq_zones.append({'type': 'resistance', 'bar': sh['index'],
                    'zone': f'{round(sh["zone_btm"],5)} — {round(sh["zone_top"],5)}',
                    'touches': sh['touch_count'], 'volume': round(sh['zone_volume'],0)})
        for sl in swing_lows[-10:]:
            if not sl['crossed'] and ci-sl['index'] <= BOS_LOOKBACK:
                liq_zones.append({'type': 'support', 'bar': sl['index'],
                    'zone': f'{round(sl["zone_btm"],5)} — {round(sl["zone_top"],5)}',
                    'touches': sl['touch_count'], 'volume': round(sl['zone_volume'],0)})

        # FVG summary (unmitigated only, recent)
        active_fvgs = [{'bar': f['index'], 'direction': f['direction'],
            'zone': f'{round(f["bottom"],5)} — {round(f["top"],5)}',
            'atr_ratio': round(f['atr_ratio'], 2)}
            for f in fvgs if not f['mitigated'] and ci - f['index'] <= BOS_LOOKBACK][-8:]

        # CHoCH summary
        recent_choch = [{'bar': ch['index'], 'direction': ch['direction'],
            'from': ch['from_trend'], 'level': round(ch['broken_level'], 5),
            'major': ch['is_major']} for ch in choch_events[-5:]]

        return convert_numpy_types({
            'symbol': symbol, 'current_price': round(cp, 5), 'data_points': int(len(df)),
            'atr': round(float(atr[ci]), 5), 'trend': trend, 'bos_bullish': int(bc), 'bos_bearish': int(sc),
            'pivot_highs': len(swing_highs), 'pivot_lows': len(swing_lows), 'total_bos': len(bos_events),
            'major_bos': sum(1 for b in bos_events if b['is_major']), 'total_sweeps': len(sweeps),
            'hp_order_blocks': len(order_blocks), 'active_obs': active_obs, 'active_obs_count': len(active_obs),
            'liquidity_zones': liq_zones,
            # NEW DATA
            'fvgs': active_fvgs, 'fvg_count': len(active_fvgs),
            'choch': recent_choch, 'choch_count': len(choch_events),
            'pd_zone': pd_zone,
            'equal_highs': eqh[:5], 'equal_lows': eql[:5],
            'eq_high_count': len(eqh), 'eq_low_count': len(eql),
            'trendlines': trendlines,
            'poc': poc_data,
            'direction': direction,
            # EXISTING
            'protected_lows': [{'price': round(p['price'],5), 'bar': p['index'], 'touches': p['touch_count']} for p in protected_lows[:3]],
            'protected_highs': [{'price': round(p['price'],5), 'bar': p['index'], 'touches': p['touch_count']} for p in protected_highs[:3]],
            'recent_bos': [{'bar': b['index'], 'direction': b['direction'], 'level': round(b['broken_level'],5),
                'major': b['is_major'], 'atr_ratio': round(b['atr_ratio'],2), 'held': b['hold_duration']} for b in bos_events[-8:]],
            'recent_sweeps': [{'bar': s['index'], 'type': s['type'], 'level': round(s['swept_level'],5),
                'deep': s['deep_sweep'], 'caused_bos': s['caused_bos']} for s in sweeps[-5:]],
            's1_signals': s1, 's2_signals': s2, 's3_signals': s3, 'all_signals': all_signals,
            'best_signal': all_signals[0] if all_signals else None,
            'signal_count': len(all_signals), 's1_count': len(s1), 's2_count': len(s2), 's3_count': len(s3)
        })
    except Exception as e:
        print(f"SMC error: {e}"); import traceback; traceback.print_exc(); return None
