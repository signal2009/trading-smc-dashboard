import numpy as np
import pandas as pd

from data import INSTRUMENTS, convert_numpy_types


def test_convert_numpy_scalars():
    assert convert_numpy_types(np.bool_(True)) is True
    assert convert_numpy_types(np.int64(3)) == 3 and isinstance(convert_numpy_types(np.int64(3)), int)
    assert isinstance(convert_numpy_types(np.float32(1.5)), float)


def test_convert_numpy_nested():
    out = convert_numpy_types({"a": np.array([1, 2]), "b": [np.int64(1), (np.float64(2.0),)], "t": pd.Timestamp("2025-01-01")})
    assert out == {"a": [1, 2], "b": [1, [2.0]], "t": "2025-01-01T00:00:00"}


def test_oil_symbols_map_to_correct_futures():
    # Regression: these two were swapped in the original single-file version.
    assert INSTRUMENTS["USOIL"] == "CL=F"   # WTI
    assert INSTRUMENTS["UKOIL"] == "BZ=F"   # Brent
