# Gold Trading Bot (XAUUSD)

A starter Python project for building, backtesting, and running a gold trading bot.

## Scope (v0)
- Data ingestion (historical + live placeholders)
- Strategy interface + sample MA crossover strategy
- Risk manager (position sizing + SL/TP)
- Paper trading executor
- Simple backtest runner

## Quick start
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m src.main --mode backtest --source yfinance --save-report
```

## Paper trading loop
```bash
python -m src.main --mode paper
```
This runs a live paper loop using yfinance prices and your risk settings.

## Next milestones
1. Connect broker/data provider
2. Add robust position sizing + SL/TP rules
3. Add live paper-trading loop
4. Add tests for strategy and risk modules

## Risk settings (.env)
- `RISK_PER_TRADE` (e.g. 0.01 = 1% equity risk per trade)
- `STOP_LOSS_PCT` (e.g. 0.01 = 1% stop)
- `TAKE_PROFIT_PCT` (e.g. 0.02 = 2% target)
- `MAX_POSITION_NOTIONAL_PCT` (cap exposure, 1.0 = 100% equity)
- `COMMISSION_BPS` (transaction fee in bps, e.g. 1.0 = 0.01%)
- `SLIPPAGE_BPS` (fill slippage in bps, e.g. 2.0 = 0.02%)

## Reporting output
Run with `--save-report` to generate files under `reports/backtest-<timestamp>/`:
- `summary.json` (performance metrics)
- `equity_curve.csv` (index-wise equity)
- `trades.csv` (trade log with entry/exit/pnl)

## Streamlit Forecast Dashboard (New)
A visual interface is included for future price prediction and charting.

### Files
- `streamlit_app.py` — Streamlit UI for historical + forecast visualization
- `requirements-streamlit.txt` — dependencies for the dashboard

### Run dashboard
```bash
pip install -r requirements-streamlit.txt
streamlit run streamlit_app.py
```

### Gold usage
- Ticker mode defaults to `GC=F` (Gold Futures)
- You can also upload your own gold price CSV (date + price columns)

Dashboard features:
- Historical price chart
- Future price forecast with confidence band
- Backtest metrics (MAE/RMSE)
- Forecast table + CSV download

## Disclaimer
This code is for education/research. Trading is risky. Use paper trading first.
