import json

from smc import analyze_smc, calculate_atr_np, detect_fvg, detect_pivots_luxalgo
from config import PIVOT_LENGTH


def test_short_history_returns_none(ohlcv):
    assert analyze_smc(ohlcv.head(50), "X") is None


def test_analyze_smc_shape_and_json(ohlcv):
    out = analyze_smc(ohlcv, "TEST")
    assert out is not None and "error" not in out
    assert out["bos_bullish"] + out["bos_bearish"] <= out["total_bos"]  # windowed counts never exceed the total
    assert out["direction"]["verdict"] in {
        "STRONG BULLISH", "BULLISH", "LEAN BULLISH", "NEUTRAL", "LEAN BEARISH", "BEARISH", "STRONG BEARISH"}
    assert -100 <= out["direction"]["direction_score"] <= 100
    json.dumps(out)


def test_analysis_is_deterministic(ohlcv):
    assert analyze_smc(ohlcv, "T") == analyze_smc(ohlcv.copy(), "T")


def test_pivots_need_length_on_both_sides(ohlcv):
    highs, lows = detect_pivots_luxalgo(ohlcv, PIVOT_LENGTH)
    n = len(ohlcv)
    for p in highs + lows:
        assert PIVOT_LENGTH <= p["index"] < n - PIVOT_LENGTH  # pivots lag by PIVOT_LENGTH bars


def test_fvg_gap_geometry(ohlcv):
    atr = calculate_atr_np(ohlcv, 14)
    for g in detect_fvg(ohlcv, atr):
        assert g["top"] > g["bottom"] and g["gap_size"] > 0
