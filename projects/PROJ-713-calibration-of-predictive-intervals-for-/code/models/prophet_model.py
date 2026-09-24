import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List
import logging
from prophet import Prophet
from prophet.diagnostics import cross_validation
from config import set_seed, SEED

logger = logging.getLogger(__name__)

class ProphetModel:
    """
    Prophet model wrapper.
    Implements seed pinning for reproducibility.
    """

    def __init__(self, uncertainty_samples: int = 1000, changepoint_prior_scale: float = 0.05):
        self.uncertainty_samples = uncertainty_samples
        self.changepoint_prior_scale = changepoint_prior_scale
        self.model = None
        self._set_seed()

    def _set_seed(self):
        """Ensure reproducibility by setting global seed."""
        set_seed(SEED)

    def fit(self, data: pd.DataFrame, date_col: str = 'ds', value_col: str = 'y') -> 'ProphetModel':
        """
        Fit the Prophet model to the data.
        
        Args:
            data: DataFrame with date and value columns
            date_col: Name of the date column
            value_col: Name of the value column
        
        Returns:
            self
        """
        self._set_seed()
        
        # Prepare data
        df = data[[date_col, value_col]].copy()
        df.columns = ['ds', 'y']
        
        # Initialize and fit model
        self.model = Prophet(
            uncertainty_samples=self.uncertainty_samples,
            changepoint_prior_scale=self.changepoint_prior_scale
        )
        
        try:
            self.model.fit(df)
        except Exception as e:
            logger.error(f"Prophet model fitting failed: {str(e)}")
            raise
        
        return self

    def predict(self, steps: int = 1, interval_width: float = 0.95) -> Dict[str, Any]:
        """
        Generate predictions and prediction intervals.
        
        Args:
            steps: Number of steps to forecast
            interval_width: Width of the prediction interval (e.g., 0.95 for 95%)
        
        Returns:
            Dictionary with 'forecast', 'lower', 'upper' keys
        """
        if self.model is None:
            raise ValueError("Model must be fitted before prediction")
        
        self._set_seed()
        
        # Create future dataframe
        future = self.model.make_future_dataframe(periods=steps, freq='D')
        forecast = self.model.predict(future)
        
        # Extract the last 'steps' predictions
        last_steps = forecast.tail(steps)
        
        return {
            'forecast': last_steps['yhat'].values,
            'lower': last_steps['yhat_lower'].values,
            'upper': last_steps['yhat_upper'].values
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
            res = self.predict(steps=steps, interval_width=level)
            intervals[level] = {
                'lower': res['lower'],
                'upper': res['upper']
            }
        return intervals
