"""Data access and shared helpers."""
import numpy as np
import pandas as pd
import yfinance as yf


def convert_numpy_types(obj):
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    return obj


INSTRUMENTS = {
    'EURUSD': 'EURUSD=X', 'GBPUSD': 'GBPUSD=X', 'USDJPY': 'USDJPY=X',
    'AUDUSD': 'AUDUSD=X', 'USDCAD': 'USDCAD=X', 'NZDUSD': 'NZDUSD=X',
    'USDCHF': 'USDCHF=X', 'EURGBP': 'EURGBP=X', 'EURJPY': 'EURJPY=X',
    'GBPJPY': 'GBPJPY=X', 'XAUUSD': 'GC=F', 'XAGUSD': 'SI=F',
    'BTCUSD': 'BTC-USD', 'ETHUSD': 'ETH-USD', 'BNBUSD': 'BNB-USD',
    'ADAUSD': 'ADA-USD', 'DOGEUSD': 'DOGE-USD', 'US30': '^DJI',
    'SPX500': '^GSPC', 'NAS100': '^IXIC', 'UKOIL': 'BZ=F', 'USOIL': 'CL=F'
}


def get_historical_data(symbol, period='6mo', interval='1h'):
    try:
        yf_symbol = INSTRUMENTS.get(symbol, symbol)
        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return None
        df = df.reset_index()
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None
