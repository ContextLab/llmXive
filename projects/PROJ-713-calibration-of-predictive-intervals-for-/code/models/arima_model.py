import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List
import logging
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.arima.model import ARIMA as StatsmodelsARIMA
from config import set_seed, SEED

logger = logging.getLogger(__name__)

class ARIMAModel:
    """
    ARIMA model wrapper using statsmodels.
    Implements seed pinning for reproducibility.
    """

    def __init__(self, order: Tuple[int, int, int] = (1, 1, 1), seasonal_order: Optional[Tuple[int, int, int, int]] = None):
        self.order = order
        self.seasonal_order = seasonal_order
        self.model = None
        self.results = None
        self._set_seed()

    def _set_seed(self):
        """Ensure reproducibility by setting global seed."""
        set_seed(SEED)

    def fit(self, data: pd.Series) -> 'ARIMAModel':
        """
        Fit the ARIMA model to the data.
        
        Args:
            data: Time series data (pandas Series)
        
        Returns:
            self
        """
        self._set_seed()
        try:
            if self.seasonal_order:
                self.model = SARIMAX(data, order=self.order, seasonal_order=self.seasonal_order)
            else:
                self.model = StatsmodelsARIMA(data, order=self.order)
            
            self.results = self.model.fit()
        except Exception as e:
            logger.error(f"ARIMA model fitting failed: {str(e)}")
            raise
        
        return self

    def predict(self, steps: int = 1, alpha: float = 0.05) -> Dict[str, Any]:
        """
        Generate predictions and prediction intervals.
        
        Args:
            steps: Number of steps to forecast
            alpha: Significance level (e.g., 0.05 for 95% interval)
        
        Returns:
            Dictionary with 'forecast', 'lower', 'upper' keys
        """
        if self.results is None:
            raise ValueError("Model must be fitted before prediction")
        
        self._set_seed()
        forecast = self.results.get_forecast(steps=steps)
        
        # Get confidence intervals
        conf_int = forecast.conf_int(alpha=alpha)
        
        return {
            'forecast': forecast.predicted_mean.values,
            'lower': conf_int.iloc[:, 0].values,
            'upper': conf_int.iloc[:, 1].values
        }

    def get_intervals(self, steps: int = 1, confidence_levels: List[float] = [0.80, 0.95]) -> Dict[str, Any]:
        """
        Generate prediction intervals for multiple confidence levels.
        
        Args:
            steps: Number of steps to forecast
            confidence_levels: List of confidence levels (e.g., [0.80, 0.95])
        
        Returns:
            Dictionary mapping confidence level to (lower, upper) arrays
        """
        intervals = {}
        for level in confidence_levels:
            alpha = 1.0 - level
            res = self.predict(steps=steps, alpha=alpha)
            intervals[level] = {
                'lower': res['lower'],
                'upper': res['upper']
            }
        return intervals
