# Trading SMC Dashboard

A small Flask dashboard for exploring markets two ways, using free Yahoo Finance data (`yfinance`, 1h bars, 3 months):

1. **Market Analysis** - EMA 20/50/200, RSI, MACD, Bollinger Bands, ATR, stochastic, support/resistance, and simple chart patterns (double bottom, head and shoulders, flag).
2. **SMC Strategy** - a Smart Money Concepts engine: LuxAlgo-style pivots (L/R 14), major BOS, CHoCH, liquidity sweeps, order blocks, fair value gaps, premium/discount (OTE), equal highs/lows, trendlines, a weighted-volume POC, a multi-factor direction verdict, and three signal strategies (continuation, structure-break reversal, recovery re-entry) with a confluence grade (A+ to D).

> **This is a research tool, not financial advice.** In my own backtests of related Liquidity Sweep and Retracement rules, no instrument showed a consistent edge across sub-windows (gold and oil lost in every sub-window; BTC and SPX had profitable windows driven by a few outlier trades). Treat the signals as hypotheses to test, not trades to take.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py        # http://127.0.0.1:5000
```

## Layout

| File | Purpose |
|---|---|
| `app.py` | Flask routes (`/`, `/api/market/<symbol>`, `/api/smc/<symbol>`) |
| `data.py` | Instrument map, `yfinance` loader, numpy/pandas JSON helper |
| `market.py` | Tab 1 indicators, patterns and signal scoring |
| `smc.py` | Tab 2 SMC detection, confluence scoring, strategies |
| `config.py` | `PIVOT_LENGTH`, `BOS_LOOKBACK` |
| `templates/index.html` | Two-tab dashboard UI |

## Known limits

- Yahoo symbols are proxies (e.g. gold = `GC=F` futures, not spot XAUUSD), and the intraday history window is short.
- `USOIL` maps to WTI futures (`CL=F`) and `UKOIL` to Brent futures (`BZ=F`); these are futures proxies, not spot.
- Pivot detection looks `PIVOT_LENGTH` bars ahead, so signals lag live price by design.

## Development with AI

Built iteratively with Claude. Working rules for AI assistants live in [`CLAUDE.md`](CLAUDE.md).
