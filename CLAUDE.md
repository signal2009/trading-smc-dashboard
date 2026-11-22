# CLAUDE.md

Rules for AI assistants working in this repo.

## Project
Flask dashboard: classic indicators (`market.py`) and a Smart Money Concepts engine (`smc.py`) over Yahoo Finance data. Run with `python app.py`.

## Rules
- **Never overwrite or modify existing saved scripts** (TradingView or otherwise). Create new files or versions instead.
- **Testing is not pass/fail.** When testing an indicator or strategy, use the data to find where and why it underperforms, and report that.
- **Be precise about pattern definitions.** Separate the "anchor level" (e.g. outside bar vs. swing pivot) from the "scan window" (same candle formation vs. forward scan). Ambiguity here has broken logic before; ask or state the assumption.
- **Prefer programmatic OHLC over reading charts visually.** Chart images and video are unreliable inputs.
- **Pivots lag.** `ta.pivothigh(high, n, n)` and `detect_pivots_luxalgo` look `n` bars forward; account for that when comparing backtests with live behaviour.
- **Document every judgment call** and every parameter loosening, with the reason.
- **Validate across instruments and non-overlapping windows**, and treat profits driven by a few outlier trades as noise, not edge. Report negative results honestly.
- **Debug silent indicators** by loosening parameters first to prove the logic can fire, then tightening step by step.
- **No secrets in the repo.** Keys, account IDs, hosts and chat IDs go in `.env` (gitignored); keep `.env.example` current.

## Layout
See the table in `README.md`.
