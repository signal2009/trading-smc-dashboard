import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def make_ohlcv(n=800, seed=1):
    """Deterministic random-walk OHLCV frame for offline tests."""
    rng = np.random.default_rng(seed)
    close = 100 + np.cumsum(rng.normal(0, 0.5, n))
    open_ = close + rng.normal(0, 0.2, n)
    high = np.maximum(open_, close) + abs(rng.normal(0, 0.3, n))
    low = np.minimum(open_, close) - abs(rng.normal(0, 0.3, n))
    volume = rng.integers(100, 1000, n)
    return pd.DataFrame({"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume})


@pytest.fixture
def ohlcv():
    return make_ohlcv()
