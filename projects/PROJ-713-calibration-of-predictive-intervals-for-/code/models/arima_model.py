"""
ARIMA model implementation for time series forecasting with predictive intervals.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List
import logging
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.arima.model import ARIMA as StatsmodelsARIMA
from utils.logger import get_logger
from utils.exceptions import ModelConvergenceError
from config import ARIMA_ORDER

logger = get_logger(__name__)

class ARIMAModel:
    """ARIMA model wrapper for forecasting with conditional variance intervals."""

    def __init__(self, order: Tuple[int, int, int] = ARIMA_ORDER):
        """
        Initialize ARIMA model.

        Args:
            order: ARIMA order (p, d, q)
        """
        self.order = order
        self.model = None
        self.results = None
        self.logger = logger

    def fit(self, train_data: pd.Series) -> None:
        """
        Fit ARIMA model to training data.

        Args:
            train_data: Training time series data
        """
        try:
            self.logger.info(f"Fitting ARIMA model with order {self.order}")
            self.model = StatsmodelsARIMA(train_data, order=self.order)
            self.results = self.model.fit()
            self.logger.info("ARIMA model fitted successfully")
        except Exception as e:
            raise ModelConvergenceError(f"ARIMA model failed to converge: {str(e)}")

    def predict_intervals(
        self,
        n_periods: int,
        conf_level: float = 0.95
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate forecasts with predictive intervals.

        Args:
            n_periods: Number of periods to forecast
            conf_level: Confidence level for intervals (default: 0.95)

        Returns:
            Tuple of (forecasts, lower_bounds, upper_bounds)
        """
        if self.results is None:
            raise ValueError("Model must be fitted before prediction")

        # Generate forecast with intervals
        forecast = self.results.get_forecast(steps=n_periods)
        conf_int = forecast.conf_int(alpha=1 - conf_level, method='conditional')

        predictions = forecast.predicted_mean.values
        lower_bounds = conf_int.iloc[:, 0].values
        upper_bounds = conf_int.iloc[:, 1].values

        return predictions, lower_bounds, upper_bounds

    def get_params(self) -> Dict[str, Any]:
        """Return model parameters."""
        return {"order": self.order}
