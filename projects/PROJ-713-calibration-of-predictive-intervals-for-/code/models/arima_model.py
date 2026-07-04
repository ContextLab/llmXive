import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List
import logging
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.arima.model import ARIMA as StatsmodelsARIMA
from config import ARIMA_ORDER, RANDOM_SEED

logger = logging.getLogger(__name__)

class ARIMAModel:
    """ARIMA model wrapper for time series forecasting."""
    
    def __init__(self, order: Tuple[int, int, int] = ARIMA_ORDER):
        self.order = order
        self.model = None
        self.results = None
        self.forecast_steps = None
        
    def fit(self, train_series: pd.Series) -> 'ARIMAModel':
        """Fit the ARIMA model to the training data.
        
        Args:
            train_series: Training time series data.
            
        Returns:
            Self for method chaining.
        """
        try:
            # Using statsmodels ARIMA (newer interface)
            self.model = StatsmodelsARIMA(train_series, order=self.order)
            self.results = self.model.fit()
            logger.info(f"ARIMA model fitted successfully. AIC: {self.results.aic}")
        except Exception as e:
            logger.error(f"ARIMA model fitting failed: {e}")
            raise
            
        return self
        
    def predict_intervals(
        self, 
        steps: int, 
        conf_int: float = 0.95
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Generate point forecasts and prediction intervals.
        
        Args:
            steps: Number of steps to forecast.
            conf_int: Confidence level for intervals (e.g., 0.95).
            
        Returns:
            Tuple of (point_forecasts, lower_bound, upper_bound).
        """
        if self.results is None:
            raise RuntimeError("Model must be fitted before prediction.")
            
        self.forecast_steps = steps
        forecast = self.results.get_forecast(steps=steps)
        
        # Get prediction intervals
        # Note: 'conditional' method is the default for ARIMA in statsmodels
        pred_int = forecast.conf_int(alpha=1 - conf_int)
        
        point_forecasts = forecast.predicted_mean.values
        lower_bound = pred_int.iloc[:, 0].values
        upper_bound = pred_int.iloc[:, 1].values
        
        return point_forecasts, lower_bound, upper_bound
