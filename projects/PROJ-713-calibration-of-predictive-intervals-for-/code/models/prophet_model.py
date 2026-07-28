"""
Prophet model implementation for time series forecasting with predictive intervals.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List
import logging
from prophet import Prophet
from prophet.diagnostics import cross_validation
from utils.logger import get_logger
from config import PROPHET_UNCERTAINTY_SAMPLES

logger = get_logger(__name__)

class ProphetModel:
    """Prophet model wrapper for forecasting with uncertainty intervals."""

    def __init__(self, uncertainty_samples: int = PROPHET_UNCERTAINTY_SAMPLES):
        """
        Initialize Prophet model.

        Args:
            uncertainty_samples: Number of samples for uncertainty estimation
        """
        self.uncertainty_samples = uncertainty_samples
        self.model = None
        self.logger = logger

    def fit(self, train_data: pd.Series) -> None:
        """
        Fit Prophet model to training data.

        Args:
            train_data: Training time series data (pd.Series with datetime index)
        """
        try:
            self.logger.info("Fitting Prophet model")

            # Convert to Prophet format
            df = train_data.reset_index()
            df.columns = ['ds', 'y']

            self.model = Prophet(
                uncertainty_samples=self.uncertainty_samples,
                yearly_seasonality='auto',
                weekly_seasonality='auto',
                daily_seasonality='auto'
            )
            self.model.fit(df)
            self.logger.info("Prophet model fitted successfully")
        except Exception as e:
            raise Exception(f"Prophet model failed to converge: {str(e)}")

    def predict_intervals(
        self,
        n_periods: int,
        conf_level: float = 0.95
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Generate forecasts with predictive intervals.

        Args:
            n_periods: Number of periods to forecast
            conf_level: Confidence level for intervals

        Returns:
            Tuple of (forecasts, lower_bounds, upper_bounds)
        """
        if self.model is None:
            raise ValueError("Model must be fitted before prediction")

        # Create future dataframe
        future = self.model.make_future_dataframe(periods=n_periods, freq='H')
        forecast = self.model.predict(future)

        # Extract last n_periods rows
        predictions = forecast['yhat'].values[-n_periods:]
        lower_bounds = forecast['yhat_lower'].values[-n_periods:]
        upper_bounds = forecast['yhat_upper'].values[-n_periods:]

        return predictions, lower_bounds, upper_bounds

    def get_params(self) -> Dict[str, Any]:
        """Return model parameters."""
        return {"uncertainty_samples": self.uncertainty_samples}
