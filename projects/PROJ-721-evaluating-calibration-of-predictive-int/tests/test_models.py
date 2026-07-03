"""
Unit tests for the model wrappers defined in ``code/models.py``.
The tests use a very short synthetic series that is sufficient to
exercise each function without requiring the full M4 dataset.
"""

import pandas as pd
import numpy as np
import pytest

from code.models import (
    arima_forecast,
    ets_forecast,
    prophet_forecast,
    lightgbm_quantile_forecast,
)


@pytest.fixture
def simple_series():
    # Monthly dummy series for 24 periods
    dates = pd.date_range(start="2020-01-01", periods=24, freq="M")
    values = np.arange(24) + np.random.normal(scale=0.1, size=24)
    return pd.Series(values, index=dates)


def test_arima_wrapper(simple_series):
    result = arima_forecast(simple_series, horizon=5)
    assert result is not None
    for key in ("point_forecast", "lower", "upper"):
        assert isinstance(result[key], np.ndarray)
        assert result[key].shape == (5,)


def test_ets_wrapper(simple_series):
    result = ets_forecast(simple_series, horizon=5)
    assert result is not None
    for key in ("point_forecast", "lower", "upper"):
        assert isinstance(result[key], np.ndarray)
        assert result[key].shape == (5,)


def test_prophet_wrapper(simple_series):
    # Prophet needs a DatetimeIndex – already satisfied by the fixture
    result = prophet_forecast(simple_series, horizon=5, interval_width=0.80)
    assert result is not None
    for key in ("point_forecast", "lower", "upper"):
        assert isinstance(result[key], np.ndarray)
        assert result[key].shape == (5,)


def test_lightgbm_wrapper(simple_series):
    result = lightgbm_quantile_forecast(simple_series, horizon=5, lags=2)
    assert result is not None
    for key in ("point_forecast", "lower", "upper"):
        assert isinstance(result[key], np.ndarray)
        assert result[key].shape == (5,)