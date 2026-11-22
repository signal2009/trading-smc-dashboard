import json

from market import analyze_market, calculate_rsi


def test_analyze_market_shape_and_json(ohlcv):
    out = analyze_market(ohlcv, "TEST")
    assert out is not None and out["symbol"] == "TEST"
    for key in ("trend", "rsi", "macd", "atr", "support_levels", "resistance_levels", "signals"):
        assert key in out
    assert 0 <= out["rsi"] <= 100
    assert out["signals"]["primary_signal"] in {"NEUTRAL", "BUY", "SELL", "STRONG BUY", "STRONG SELL"}
    json.dumps(out)  # must be JSON-serialisable for the API


def test_analyze_market_empty_returns_none():
    assert analyze_market(None, "X") is None


def test_rsi_bounded(ohlcv):
    rsi = calculate_rsi(ohlcv["Close"]).dropna()
    assert ((rsi >= 0) & (rsi <= 100)).all()
