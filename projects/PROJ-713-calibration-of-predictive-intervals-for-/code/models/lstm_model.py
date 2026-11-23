import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List
import logging
import torch
import torch.nn as nn
import os
import json
from pathlib import Path
from utils.logger import get_logger
from utils.exceptions import ModelConvergenceError, DataValidationError
from config import PROJECT_ROOT, RESULTS_DIR

logger = get_logger(__name__)

# Ensure results directory exists
RESULTS_PATH = Path(PROJECT_ROOT) / RESULTS_DIR
RESULTS_PATH.mkdir(parents=True, exist_ok=True)
SKIPPED_LOG_PATH = RESULTS_PATH / "skipped_series.log"

class TimeSeriesLSTM(nn.Module):
    """
    Single hidden layer LSTM for time series forecasting.
    Architecture: Input -> LSTM(32 units) -> Dense -> Output
    """
    def __init__(self, input_size: int, hidden_size: int = 32, output_size: int = 1):
        super(TimeSeriesLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(self, x):
        # x shape: (batch, seq_len, input_size)
        lstm_out, (h_n, c_n) = self.lstm(x)
        # Take the last time step output
        last_out = lstm_out[:, -1, :]
        out = self.fc(last_out)
        return out

class LSTMModel:
    """
    Wrapper for LSTM time series model with interval generation.
    Implements retry logic with reduced learning rate and fallback to 
    residual-based Gaussian intervals on failure.
    """
    
    def __init__(
        self,
        input_size: int = 1,
        hidden_size: int = 32,
        max_epochs: int = 50,
        patience: int = 5,
        learning_rate: float = 0.001,
        batch_size: int = 32,
        forecast_horizon: int = 1
    ):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.max_epochs = max_epochs
        self.patience = patience
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.forecast_horizon = forecast_horizon
        
        self.model = TimeSeriesLSTM(input_size, hidden_size)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        self.history = []
        self.is_fitted = False
        
    def _prepare_sequences(self, data: np.ndarray, seq_length: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare time series data for LSTM training.
        Returns: X (samples, seq_len, input_size), y (samples, forecast_horizon)
        """
        X, y = [], []
        for i in range(len(data) - seq_length - self.forecast_horizon + 1):
            X.append(data[i:i+seq_length])
            y.append(data[i+seq_length:i+seq_length+self.forecast_horizon])
        
        return np.array(X), np.array(y)

    def _train_model(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        lr: float
    ) -> bool:
        """
        Train the LSTM model with early stopping.
        Returns True if training converges successfully, False otherwise.
        """
        self.model = TimeSeriesLSTM(self.input_size, self.hidden_size).to(self.device)
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        
        X_train_t = torch.FloatTensor(X_train).to(self.device)
        y_train_t = torch.FloatTensor(y_train).to(self.device)
        X_val_t = torch.FloatTensor(X_val).to(self.device)
        y_val_t = torch.FloatTensor(y_val).to(self.device)
        
        best_val_loss = float('inf')
        patience_counter = 0
        self.history = []
        
        try:
            for epoch in range(self.max_epochs):
                self.model.train()
                optimizer.zero_grad()
                
                # Mini-batch training
                indices = torch.randperm(len(X_train_t))
                epoch_loss = 0
                num_batches = 0
                
                for i in range(0, len(X_train_t), self.batch_size):
                    batch_idx = indices[i:i+self.batch_size]
                    batch_X = X_train_t[batch_idx]
                    batch_y = y_train_t[batch_idx]
                    
                    pred = self.model(batch_X)
                    loss = criterion(pred, batch_y)
                    
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                    optimizer.step()
                    
                    epoch_loss += loss.item()
                    num_batches += 1
                
                avg_train_loss = epoch_loss / num_batches
                
                # Validation
                self.model.eval()
                with torch.no_grad():
                    val_pred = self.model(X_val_t)
                    val_loss = criterion(val_pred, y_val_t).item()
                
                self.history.append({
                    'epoch': epoch,
                    'train_loss': avg_train_loss,
                    'val_loss': val_loss
                })
                
                logger.debug(f"Epoch {epoch}: Train Loss: {avg_train_loss:.6f}, Val Loss: {val_loss:.6f}")
                
                # Early stopping
                if val_loss < best_val_loss - 1e-6:
                    best_val_loss = val_loss
                    patience_counter = 0
                    # Save best model state
                    self.best_state = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}
                else:
                    patience_counter += 1
                
                if patience_counter >= self.patience:
                    logger.info(f"Early stopping at epoch {epoch}")
                    break
            
            # Restore best model
            if hasattr(self, 'best_state'):
                self.model.load_state_dict(self.best_state)
            
            self.is_fitted = True
            return True
            
        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            return False

    def _generate_residual_intervals(
        self,
        train_residuals: np.ndarray,
        forecast_point: np.ndarray,
        level: float = 0.95
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate prediction intervals based on residual distribution.
        """
        if len(train_residuals) == 0:
            raise ValueError("No residuals available for interval estimation")
        
        alpha = 1 - level
        lower_quantile = alpha / 2
        upper_quantile = 1 - alpha / 2
        
        lower_margin = np.quantile(train_residuals, lower_quantile)
        upper_margin = np.quantile(train_residuals, upper_quantile)
        
        lower_bound = forecast_point + lower_margin
        upper_bound = forecast_point + upper_margin
        
        return lower_bound, upper_bound

    def fit(
        self,
        series: np.ndarray,
        train_ratio: float = 0.8,
        seq_length: int = 24,
        series_id: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Fit the LSTM model to the time series.
        Implements retry logic with reduced learning rate.
        Returns training metadata including fallback status.
        """
        n = len(series)
        train_size = int(n * train_ratio)
        
        # Prepare training data
        X_train, y_train = self._prepare_sequences(series[:train_size], seq_length)
        X_val, y_val = self._prepare_sequences(series[:train_size], seq_length)
        
        # Ensure we have enough data
        if len(X_train) < 10:
            raise DataValidationError(
                f"Series {series_id} has insufficient data for LSTM training. "
                f"Need at least {seq_length + 10} points, got {len(series)}"
            )
        
        # Split training and validation
        val_size = max(1, len(X_train) // 5)
        X_tr, y_tr = X_train[:-val_size], y_train[:-val_size]
        X_vl, y_vl = X_train[-val_size:], y_train[-val_size:]
        
        # Retry logic
        learning_rates = [self.learning_rate, self.learning_rate * 0.1, self.learning_rate * 0.01]
        max_retries = 2
        success = False
        last_error = None
        
        for attempt in range(max_retries + 1):
            lr = learning_rates[min(attempt, len(learning_rates) - 1)]
            logger.info(f"Attempting LSTM training for series {series_id}, attempt {attempt + 1}, lr={lr}")
            
            success = self._train_model(X_tr, y_tr, X_vl, y_vl, lr)
            
            if success:
                logger.info(f"LSTM training succeeded for series {series_id} on attempt {attempt + 1}")
                break
            
            last_error = f"Training failed with lr={lr}"
            logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
        
        result = {
            'series_id': series_id,
            'model': 'LSTM',
            'success': success,
            'fallback_applied': False,
            'failure_reason': None,
            'final_lr': learning_rates[-1] if not success else learning_rates[min(max_retries, len(learning_rates) - 1)],
            'epochs_run': len(self.history) if hasattr(self, 'history') else 0
        }
        
        if not success:
            result['failure_reason'] = last_error or "Unknown training failure"
            result['fallback_applied'] = True
            
            # Log to skipped_series.log
            log_entry = {
                'series_id': series_id,
                'model': 'LSTM',
                'failure_reason': result['failure_reason'],
                'fallback_applied': True,
                'timestamp': pd.Timestamp.now().isoformat()
            }
            
            with open(SKIPPED_LOG_PATH, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            logger.warning(f"LSTM failed for series {series_id}. Fallback will be used.")
        
        return result

    def predict(
        self,
        series: np.ndarray,
        seq_length: int = 24,
        forecast_horizon: Optional[int] = None,
        use_fallback: bool = False,
        series_id: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Generate point forecasts and prediction intervals.
        If use_fallback is True, uses residual-based Gaussian intervals.
        """
        if forecast_horizon is None:
            forecast_horizon = self.forecast_horizon
        
        if use_fallback:
            # Fallback: use simple residual-based intervals
            logger.info(f"Using fallback interval estimation for series {series_id}")
            
            # Generate point forecast (simple last value + small noise estimate)
            point_forecast = series[-1]
            
            # Estimate residuals from last few observations
            if len(series) > seq_length:
                recent = series[-seq_length:]
                residuals = np.diff(recent)
                residual_std = np.std(residuals) if len(residuals) > 0 else 0.1
            else:
                residual_std = 0.1
            
            # Generate intervals for different confidence levels
            intervals = {}
            for level in [0.80, 0.95]:
                alpha = 1 - level
                margin = np.quantile(np.abs(np.random.normal(0, residual_std, 10000)), 1 - alpha/2)
                intervals[level] = {
                    'lower': point_forecast - margin,
                    'upper': point_forecast + margin
                }
            
            return {
                'series_id': series_id,
                'point_forecast': point_forecast,
                'intervals': intervals,
                'method': 'fallback_residual_gaussian'
            }
        
        if not self.is_fitted:
            raise ModelConvergenceError(f"Model not fitted. Call fit() first.")
        
        # Prepare input sequence
        if len(series) < seq_length:
            raise DataValidationError(
                f"Insufficient data for prediction. Need {seq_length} points, got {len(series)}"
            )
        
        input_seq = series[-seq_length:].reshape(1, seq_length, 1)
        input_tensor = torch.FloatTensor(input_seq).to(self.device)
        
        # Generate prediction
        self.model.eval()
        with torch.no_grad():
            forecast = self.model(input_tensor).cpu().numpy().flatten()
        
        # Estimate residuals from training history if available
        # For simplicity, use a heuristic based on forecast magnitude
        residual_std = np.std(series[-seq_length:]) * 0.1  # Heuristic estimate
        
        intervals = {}
        for level in [0.80, 0.95]:
            alpha = 1 - level
            z_score = 1.96 if level == 0.95 else 1.28
            margin = z_score * residual_std * np.sqrt(forecast_horizon)
            intervals[level] = {
                'lower': forecast[0] - margin,
                'upper': forecast[0] + margin
            }
        
        return {
            'series_id': series_id,
            'point_forecast': forecast[0],
            'intervals': intervals,
            'method': 'lstm'
        }

    def get_intervals(
        self,
        series: np.ndarray,
        level: float = 0.95,
        seq_length: int = 24,
        series_id: str = "unknown",
        use_fallback: bool = False
    ) -> Tuple[float, float]:
        """
        Convenience method to get prediction intervals for a specific level.
        """
        result = self.predict(
            series=series,
            seq_length=seq_length,
            use_fallback=use_fallback,
            series_id=series_id
        )
        
        if level not in result['intervals']:
            raise ValueError(f"Level {level} not in available intervals: {list(result['intervals'].keys())}")
        
        return (
            result['intervals'][level]['lower'],
            result['intervals'][level]['upper']
        )