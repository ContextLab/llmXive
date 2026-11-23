"""
Diagnostics‑related unit tests.

These tests exercise the VIF calculation helper in `code/diagnostics.py`
using a tiny, well‑conditioned design matrix.
"""

import pandas as pd
import pytest

from code.diagnostics import calculate_vif

def test_calculate_vif_returns_dataframe():
    # Simple design matrix with two uncorrelated predictors.
    X = pd.DataFrame({
        "precipitation": [0.0, 0.1, 0.0, 0.2],
        "visibility": [10, 8, 9, 7],
        "temperature": [30, 28, 29, 27],
    })
    vif_df = calculate_vif(X)

    # The result should be a DataFrame with the same index as the columns.
    assert isinstance(vif_df, pd.DataFrame)
    assert list(vif_df.index) == list(X.columns)
    # VIF values for a tiny, non‑collinear matrix should be close to 1.
    for value in vif_df["VIF"]:
        assert value < 5.0