"""Unit tests for the refactored model fitting pipeline."""
from __future__ import annotations

import pathlib

import pandas as pd
import pytest

from analysis.model_fitting import (
    fit_linear_model,
    fit_polynomial_model,
    fit_logarithmic_model,
)


@pytest.fixture
def sample_df(tmp_path: pathlib.Path) -> pd.DataFrame:
    """Create a tiny realistic dataframe for quick testing."""
    data = {
        "knot_id": ["K1", "K2", "K3", "K4"],
        "crossing_number": [5, 6, 7, 8],
        "braid_index": [3, 4, 5, 6],
        "hyperbolic_volume": [2.1, 2.5, 3.0, 3.6],
        "family": ["A", "A", "B", "B"],
    }
    return pd.DataFrame(data)


def test_fit_linear(sample_df: pd.DataFrame) -> None:
    res = fit_linear_model(sample_df)
    assert res.name == "Linear"
    assert hasattr(res, "metrics")
    assert res.metrics.r_squared >= 0.0


def test_fit_polynomial(sample_df: pd.DataFrame) -> None:
    res = fit_polynomial_model(sample_df, degree=2)
    assert "Polynomial" in res.name
    assert res.metrics.mae >= 0.0


def test_fit_logarithmic(sample_df: pd.DataFrame) -> None:
    res = fit_logarithmic_model(sample_df)
    assert res.name == "Logarithmic"
    # VIF should be a dict (even if empty) per the implementation contract
    assert isinstance(res.metrics.vif, dict)