import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List
import logging
from prophet import Prophet
from prophet.diagnostics import cross_validation
from config import PROPHET_UNCERTAINTY_SAMPLES, RANDOM_SEED

logger = logging.getLogger(__name__)

class ProphetModel:
    """Prophet model wrapper for time series forecasting."""
    
    def __init__(self, uncertainty_samples: int = PROPHET_UNCERTAINTY_SAMPLES):
        self.uncertainty_samples = uncertainty_samples
        self.model = None
        self.forecast = None
        
    def fit(self, train_series: pd.Series) -> 'ProphetModel':
        """Fit the Prophet model to the training data.
        
        Args:
            train_series: Training time series data (pd.Series with DatetimeIndex).
            
        Returns:
            Self for method chaining.
        """
        try:
            # Convert series to Prophet format
            df = train_series.reset_index()
            if len(df.columns) == 2:
                df.columns = ['ds', 'y']
            else:
                # Ensure columns are named correctly
                df = df.iloc[:, :2]
                df.columns = ['ds', 'y']
                
            self.model = Prophet(
                uncertainty_samples=self.uncertainty_samples,
                seed=RANDOM_SEED
            )
            self.model.fit(df)
            logger.info("Prophet model fitted successfully.")
        except Exception as e:
            logger.error(f"Prophet model fitting failed: {e}")
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
        if self.model is None:
            raise RuntimeError("Model must be fitted before prediction.")
            
        # Create future dataframe
        last_date = self.model.history['ds'].max()
        future = self.model.make_future_dataframe(periods=steps, freq='H')
        
        # Predict
        forecast = self.model.predict(future)
        self.forecast = forecast
        
        # Extract recent forecasts
        recent_forecast = forecast.tail(steps)
        
        point_forecasts = recent_forecast['yhat'].values
        lower_bound = recent_forecast[f'yhat_lower'].values
        upper_bound = recent_forecast[f'yhat_upper'].values
        
        return point_forecasts, lower_bound, upper_bound
