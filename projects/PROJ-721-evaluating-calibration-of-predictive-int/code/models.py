"""
models.py
------------

Python‑only wrappers for a set of forecasting models used in the
calibration evaluation pipeline.

The public interface consists of four functions, each taking a
``pandas.Series`` of training observations and returning a dictionary
with point forecasts and prediction interval bounds.

All functions are deliberately lightweight – they use only the
Python ecosystem (no R back‑ends) and are equipped with defensive
error handling.  If a model fails to converge or raises a warning,
the function logs the issue and returns ``None`` so the pipeline can
continue gracefully.

Returned dictionary format
--------------------------

::
    {
        "point_forecast": np.ndarray,   # shape (horizon,)
        "lower":          np.ndarray,   # shape (horizon,)
        "upper":          np.ndarray,   # shape (horizon,)
    }

where ``horizon`` is the number of steps ahead to predict.
"""

from __future__ import annotations

import logging
import warnings
from typing import Dict, Optional

import numpy as np
import pandas as pd

# statsmodels for ARIMA and ETS
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# Prophet – try the modern ``prophet`` package first, fall back to ``fbprophet``
try:
    from prophet import Prophet  # type: ignore
except Exception:  # pragma: no cover
    from fbprophet import Prophet  # type: ignore

# LightGBM for quantile regression
from lightgbm import LGBMRegressor

__all__ = [
    "arima_forecast",
    "ets_forecast",
    "prophet_forecast",
    "lightgbm_quantile_forecast",
]

logger = logging.getLogger(__name__)
if not logger.handlers:
    # Ensure at least one handler exists so that log messages are not lost
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def _ensure_series(series: pd.Series) -> pd.Series:
    """
    Validate input series and coerce to a pandas Series with a numeric dtype.

    Parameters
    ----------
    series: pd.Series
        Time‑series observations.

    Returns
    -------
    pd.Series
        Cleaned series.

    Raises
    ------
    ValueError
        If the series is empty or non‑numeric.
    """
    if not isinstance(series, pd.Series):
        raise TypeError("Input must be a pandas Series.")
    if series.empty:
        raise ValueError("Input series must contain at least one observation.")
    # Force numeric dtype; raise if conversion fails
    series = pd.to_numeric(series, errors="raise")
    return series


def arima_forecast(
    series: pd.Series,
    horizon: int = 12,
    order: tuple[int, int, int] = (1, 1, 1),
    seasonal_order: tuple[int, int, int, int] = (1, 1, 1, 12),
) -> Optional[Dict[str, np.ndarray]]:
    """
    Fit an ARIMA model (SARIMAX) and generate forecasts.

    The model uses a fixed order of (1,1,1) and seasonal order
    (1,1,1,12) unless overridden.

    Parameters
    ----------
    series : pd.Series
        Training data.
    horizon : int, default 12
        Number of steps ahead to forecast.
    order : tuple, default (1, 1, 1)
        ARIMA (p,d,q) order.
    seasonal_order : tuple, default (1, 1, 1, 12)
        Seasonal (P,D,Q,s) order.

    Returns
    -------
    dict or None
        Dictionary with ``point_forecast``, ``lower`` and ``upper`` arrays,
        or ``None`` if the model fails to converge.
    """
    series = _ensure_series(series)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            model = SARIMAX(
                series,
                order=order,
                seasonal_order=seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            )
            results = model.fit(disp=False)
        except Exception as exc:  # pragma: no cover
            logger.error(f"ARIMA fitting error: {exc}")
            return None

        # Detect convergence warnings
        for warning in w:
            if issubclass(warning.category, UserWarning) or issubclass(
                warning.category, RuntimeWarning
            ):
                logger.warning(f"ARIMA warning: {warning.message}")

    # Forecast with confidence intervals (default 95%)
    forecast = results.get_forecast(steps=horizon)
    conf_int = forecast.conf_int(alpha=0.05)  # 95% CI → lower/upper
    point = forecast.predicted_mean.values
    lower = conf_int.iloc[:, 0].values
    upper = conf_int.iloc[:, 1].values

    return {"point_forecast": point, "lower": lower, "upper": upper}


def ets_forecast(
    series: pd.Series,
    horizon: int = 12,
    trend: str = "add",
    seasonal: str = "add",
    seasonal_periods: int = 12,
) -> Optional[Dict[str, np.ndarray]]:
    """
    Fit an Exponential Smoothing (ETS) model and generate forecasts.

    Parameters
    ----------
    series : pd.Series
        Training data.
    horizon : int, default 12
        Forecast horizon.
    trend : str, default 'add'
        Trend component ('add', 'mul', or None).
    seasonal : str, default 'add'
        Seasonal component ('add', 'mul', or None).
    seasonal_periods : int, default 12
        Length of the seasonal cycle.

    Returns
    -------
    dict or None
        Forecast dictionary or ``None`` on failure.
    """
    series = _ensure_series(series)

    try:
        model = ExponentialSmoothing(
            series,
            trend=trend,
            seasonal=seasonal,
            seasonal_periods=seasonal_periods,
        )
        fitted = model.fit(optimized=True)
    except Exception as exc:  # pragma: no cover
        logger.error(f"ETS fitting error: {exc}")
        return None

    forecast = fitted.forecast(horizon)
    # statsmodels ETS does not provide prediction intervals directly.
    # As a simple proxy we use the in‑sample residual standard deviation.
    resid = series - fitted.fittedvalues
    sigma = np.std(resid, ddof=1)

    # 95% normal‑based interval
    lower = forecast - 1.96 * sigma
    upper = forecast + 1.96 * sigma

    return {
        "point_forecast": forecast.values,
        "lower": lower.values,
        "upper": upper.values,
    }


def prophet_forecast(
    series: pd.Series,
    horizon: int = 12,
    interval_width: float = 0.80,
    seasonality_mode: str = "multiplicative",
    changepoint_prior_scale: float = 0.05,
) -> Optional[Dict[str, np.ndarray]]:
    """
    Fit a Prophet model and generate forecasts.

    Parameters
    ----------
    series : pd.Series
        Training data indexed by datetime‑like values.
    horizon : int, default 12
        Number of periods to predict.
    interval_width : float, default 0.80
        Desired width of the prediction interval (e.g., 0.80 for 80%).
    seasonality_mode : str, default 'multiplicative'
        Seasonality mode for Prophet.
    changepoint_prior_scale : float, default 0.05
        Flexibility of the trend changepoints.

    Returns
    -------
    dict or None
        Forecast dictionary or ``None`` if fitting fails.
    """
    if not isinstance(series.index, pd.DatetimeIndex):
        logger.error("Prophet requires a DatetimeIndex on the Series.")
        return None

    series = _ensure_series(series)

    df = pd.DataFrame({"ds": series.index, "y": series.values})

    try:
        m = Prophet(
            interval_width=interval_width,
            seasonality_mode=seasonality_mode,
            changepoint_prior_scale=changepoint_prior_scale,
        )
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=UserWarning)
            m.fit(df)
    except Exception as exc:  # pragma: no cover
        logger.error(f"Prophet fitting error: {exc}")
        return None

    future = m.make_future_dataframe(periods=horizon, freq=pd.infer_freq(series.index))
    forecast = m.predict(future)

    # Take only the newly forecasted rows
    new_rows = forecast.tail(horizon)

    point = new_rows["yhat"].values
    lower = new_rows["yhat_lower"].values
    upper = new_rows["yhat_upper"].values

    return {"point_forecast": point, "lower": lower, "upper": upper}


def _prepare_lag_features(series: pd.Series, lags: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """
    Simple utility to create lagged features for LightGBM.

    Parameters
    ----------
    series : pd.Series
        Training observations.
    lags : int, default 1
        Number of lagged observations to use as features.

    Returns
    -------
    X, y : np.ndarray
        Feature matrix and target vector.
    """
    y = series.values[lags:]
    X = np.column_stack([series.values[i : len(series) - lags + i] for i in range(lags)])
    return X, y


def lightgbm_quantile_forecast(
    series: pd.Series,
    horizon: int = 12,
    lower_alpha: float = 0.10,
    upper_alpha: float = 0.90,
    lags: int = 1,
    **lgb_kwargs,
) -> Optional[Dict[str, np.ndarray]]:
    """
    LightGBM quantile regression for prediction intervals.

    Two separate models are trained, one for the lower quantile and one
    for the upper quantile.  The point forecast is taken as the median
    (quantile 0.5) model.

    Parameters
    ----------
    series : pd.Series
        Training data.
    horizon : int, default 12
        Forecast horizon.
    lower_alpha : float, default 0.10
        Lower quantile (e.g., 0.10 for an 80% interval).
    upper_alpha : float, default 0.90
        Upper quantile.
    lags : int, default 1
        Number of lagged values used as features.
    **lgb_kwargs
        Additional keyword arguments passed to ``LGBMRegressor``.

    Returns
    -------
    dict or None
        Forecast dictionary or ``None`` on failure.
    """
    series = _ensure_series(series)

    if len(series) <= lags:
        logger.error("Series too short for the requested number of lags.")
        return None

    X_train, y_train = _prepare_lag_features(series, lags=lags)

    # Helper to fit a quantile model
    def _fit_quantile(alpha: float) -> LGBMRegressor:
        params = {
            "objective": "quantile",
            "alpha": alpha,
            "n_estimators": 100,
            "learning_rate": 0.1,
            "verbosity": -1,
        }
        params.update(lgb_kwargs)
        return LGBMRegressor(**params)

    try:
        lower_model = _fit_quantile(lower_alpha).fit(X_train, y_train)
        upper_model = _fit_quantile(upper_alpha).fit(X_train, y_train)
        median_model = _fit_quantile(0.5).fit(X_train, y_train)
    except Exception as exc:  # pragma: no cover
        logger.error(f"LightGBM fitting error: {exc}")
        return None

    # Prepare features for future timestamps
    last_vals = series.values[-lags:]
    forecasts = {"point_forecast": [], "lower": [], "upper": []}
    current = list(last_vals)

    for _ in range(horizon):
        X_next = np.array(current[-lags:]).reshape(1, -1)
        point = median_model.predict(X_next)[0]
        lower = lower_model.predict(X_next)[0]
        upper = upper_model.predict(X_next)[0]

        forecasts["point_forecast"].append(point)
        forecasts["lower"].append(lower)
        forecasts["upper"].append(upper)

        # Append point forecast to the rolling window for next step
        current.append(point)

    return {
        "point_forecast": np.array(forecasts["point_forecast"]),
        "lower": np.array(forecasts["lower"]),
        "upper": np.array(forecasts["upper"]),
    }
