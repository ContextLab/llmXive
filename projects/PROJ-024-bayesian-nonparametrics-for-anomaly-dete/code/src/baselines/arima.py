"""
ARIMA Baseline Model for Time Series Anomaly Detection.

Implements ARIMA (AutoRegressive Integrated Moving Average) as a baseline
model for comparison against the DPGMM detector. This baseline uses
residuals from ARIMA predictions to identify anomalies.

Per US2 acceptance scenario 1: Compare DPGMM detector against ARIMA,
moving average, and LSTM Autoencoder baselines on public benchmarks
with F1-score validation.

API Surface:
  - ARIMAConfig: Configuration dataclass
  - ARIMAPrediction: Prediction output dataclass
  - ARIMABaseline: Main baseline class
  - create_baseline: Factory function
  - main: Entry point for CLI execution

Imports from API surface:
  - numpy as np
  - dataclasses: dataclass, field
  - typing: Optional, List, Dict, Any, Tuple, Union
  - datetime
  - pathlib.Path
  - sys
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, Union
from datetime import datetime
from pathlib import Path
import sys
import logging
import json

# Try to import statsmodels, fall back to simple AR implementation
try:
    from statsmodels.tsa.arima.model import ARIMA as StatsModelsARIMA
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    logging.warning("statsmodels not available, using simple AR implementation")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ARIMAConfig:
    """Configuration for ARIMA baseline model.

    Attributes:
        order: ARIMA order (p, d, q) - number of AR terms, differencing order, MA terms
        seasonal_order: Seasonal order (P, D, Q, s) - None for non-seasonal
        trend: Trend parameter ('c', 't', 'ct', or '')
        enforce_stationarity: Whether to enforce stationarity constraints
        enforce_invertibility: Whether to enforce invertibility constraints
        maxiter: Maximum number of iterations for optimization
        start_params: Initial parameter values (optional)
        random_state: Random seed for reproducibility
        threshold: Anomaly threshold (number of standard deviations)
        training_window: Number of initial points for training
        validation_window: Number of points for threshold calibration
    """
    order: Tuple[int, int, int] = (1, 1, 1)
    seasonal_order: Optional[Tuple[int, int, int, int]] = None
    trend: str = 'c'
    enforce_stationarity: bool = True
    enforce_invertibility: bool = True
    maxiter: int = 100
    start_params: Optional[List[float]] = None
    random_state: int = 42
    threshold: float = 3.0
    training_window: int = 100
    validation_window: int = 50

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for serialization."""
        return {
            'order': list(self.order),
            'seasonal_order': list(self.seasonal_order) if self.seasonal_order else None,
            'trend': self.trend,
            'enforce_stationarity': self.enforce_stationarity,
            'enforce_invertibility': self.enforce_invertibility,
            'maxiter': self.maxiter,
            'start_params': self.start_params,
            'random_state': self.random_state,
            'threshold': self.threshold,
            'training_window': self.training_window,
            'validation_window': self.validation_window
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ARIMAConfig':
        """Create config from dictionary."""
        if 'order' in data and isinstance(data['order'], list):
            data['order'] = tuple(data['order'])
        if 'seasonal_order' in data and data['seasonal_order'] is not None:
            data['seasonal_order'] = tuple(data['seasonal_order'])
        return cls(**data)


@dataclass
class ARIMAPrediction:
    """Prediction output from ARIMA baseline.

    Attributes:
        timestamp: Timestamp of the prediction
        observed_value: Actual observed value
        predicted_value: ARIMA predicted value
        residual: Residual (observed - predicted)
        anomaly_score: Absolute residual or custom score
        is_anomaly: Boolean flag for anomaly
        confidence_interval_lower: Lower bound of prediction interval
        confidence_interval_upper: Upper bound of prediction interval
        model_params: Current model parameters (for inspection)
    """
    timestamp: datetime
    observed_value: float
    predicted_value: float
    residual: float
    anomaly_score: float
    is_anomaly: bool
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    model_params: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert prediction to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'observed_value': float(self.observed_value),
            'predicted_value': float(self.predicted_value),
            'residual': float(self.residual),
            'anomaly_score': float(self.anomaly_score),
            'is_anomaly': bool(self.is_anomaly),
            'confidence_interval_lower': float(self.confidence_interval_lower) if self.confidence_interval_lower else None,
            'confidence_interval_upper': float(self.confidence_interval_upper) if self.confidence_interval_upper else None,
            'model_params': self.model_params
        }


class ARIMABaseline:
    """ARIMA-based baseline for time series anomaly detection.

    This class implements an ARIMA model that:
    1. Trains on an initial window of observations
    2. Makes one-step-ahead predictions for subsequent observations
    3. Computes residuals and anomaly scores based on prediction errors
    4. Calibrates threshold using validation data

    Per US2 acceptance scenario 1: Provides comparison baseline against
    DPGMM model with F1-score validation on public benchmarks.

    Attributes:
        config: ARIMAConfig with model parameters
        model: Fitted ARIMA model (statsmodels or custom)
        training_data: Historical observations used for training
        residual_std: Standard deviation of residuals for scoring
        threshold: Anomaly threshold in standard deviations
        is_fitted: Whether model has been trained
        prediction_history: List of all predictions made
    """

    def __init__(self, config: Optional[ARIMAConfig] = None):
        """Initialize ARIMA baseline with configuration.

        Args:
            config: ARIMAConfig instance. Uses defaults if None.
        """
        self.config = config or ARIMAConfig()
        self.model = None
        self.training_data = []
        self.residual_std = None
        self.threshold = self.config.threshold
        self.is_fitted = False
        self.prediction_history = []
        self._rng = np.random.default_rng(self.config.random_state)

        # Track residual statistics for threshold calibration
        self._residuals = []
        self._residual_mean = 0.0
        self._residual_variance = 0.0

    def fit(self, training_data: Union[List[float], np.ndarray],
            validation_data: Optional[Union[List[float], np.ndarray]] = None) -> 'ARIMABaseline':
        """Fit ARIMA model on training data and calibrate threshold.

        Args:
            training_data: Historical observations for model fitting
            validation_data: Optional data for threshold calibration

        Returns:
            Self for method chaining
        """
        training_data = np.asarray(training_data, dtype=np.float64)

        if len(training_data) < self.config.training_window:
            logger.warning(f"Training data length {len(training_data)} < minimum {self.config.training_window}")
            self.training_data = training_data.tolist()
            self.is_fitted = True
            return self

        self.training_data = training_data[:self.config.training_window].tolist()

        if HAS_STATSMODELS:
            self._fit_statsmodels(training_data)
        else:
            self._fit_simple_ar(training_data)

        # Calibrate threshold if validation data provided
        if validation_data is not None:
            self._calibrate_threshold(validation_data)

        self.is_fitted = True
        return self

    def _fit_statsmodels(self, training_data: np.ndarray) -> None:
        """Fit model using statsmodels ARIMA."""
        try:
            # Handle small datasets
            if len(training_data) < 10:
                logger.warning("Dataset too small for statsmodels ARIMA, using simple AR")
                self._fit_simple_ar(training_data)
                return

            self.model = StatsModelsARIMA(
                training_data,
                order=self.config.order,
                seasonal_order=self.config.seasonal_order,
                trend=self.config.trend,
                enforce_stationarity=self.config.enforce_stationarity,
                enforce_invertibility=self.config.enforce_invertibility,
                start_params=self.config.start_params
            )
            self.model_fit = self.model.fit(maxiter=self.config.maxiter)
            logger.info(f"ARIMA model fitted with order {self.config.order}")

            # Estimate residual standard deviation
            residuals = self.model_fit.resid
            self.residual_std = np.std(residuals) if len(residuals) > 0 else 1.0

        except Exception as e:
            logger.warning(f"statsmodels ARIMA failed: {e}, falling back to simple AR")
            self._fit_simple_ar(training_data)

    def _fit_simple_ar(self, training_data: np.ndarray) -> None:
        """Fit simple AR model as fallback."""
        p = self.config.order[0]
        n = len(training_data)

        if n <= p:
            logger.warning(f"Not enough data for AR({p}), using mean model")
            self._simple_ar_coeffs = [0.0]
            self._simple_ar_intercept = float(np.mean(training_data))
            self.residual_std = np.std(training_data)
            self.model = None
            return

        # Build design matrix for AR(p)
        X = []
        y = []
        for i in range(p, n):
            X.append(training_data[i-p:i][::-1])  # Reverse for proper lag ordering
            y.append(training_data[i])

        X = np.asarray(X)
        y = np.asarray(y)

        # Add intercept
        X = np.column_stack([np.ones(len(X)), X])

        # Solve least squares
        try:
            coeffs, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
            self._simple_ar_intercept = coeffs[0]
            self._simple_ar_coeffs = coeffs[1:].tolist()
        except np.linalg.LinAlgError:
            # Fallback to mean model
            self._simple_ar_coeffs = [0.0] * p
            self._simple_ar_intercept = float(np.mean(training_data))

        # Estimate residual standard deviation
        predictions = self._predict_ar(training_data[:-1])
        residuals = training_data[p:] - predictions
        self.residual_std = np.std(residuals) if len(residuals) > 0 else 1.0

        self.model = None  # Mark as using simple AR

    def _predict_ar(self, data: Union[List[float], np.ndarray]) -> np.ndarray:
        """Make predictions using simple AR model."""
        data = np.asarray(data, dtype=np.float64)
        p = len(self._simple_ar_coeffs)

        if p == 0:
            return np.full(len(data), self._simple_ar_intercept)

        predictions = []
        for i in range(p, len(data)):
            pred = self._simple_ar_intercept
            for j, coeff in enumerate(self._simple_ar_coeffs):
                pred += coeff * data[i - j - 1]
            predictions.append(pred)

        return np.asarray(predictions)

    def _calibrate_threshold(self, validation_data: Union[List[float], np.ndarray]) -> None:
        """Calibrate anomaly threshold using validation data.

        Uses residuals on validation data to estimate appropriate threshold.

        Args:
            validation_data: Data for threshold calibration
        """
        validation_data = np.asarray(validation_data, dtype=np.float64)

        # Generate predictions on validation data
        all_data = np.array(self.training_data + validation_data.tolist())

        if HAS_STATSMODELS and self.model is not None:
            try:
                forecasts = self.model_fit.get_forecast(steps=len(validation_data))
                predicted = forecasts.predicted_mean.values
                conf_int = forecasts.conf_int()
            except Exception:
                predicted = self._predict_ar(all_data)[len(self.training_data):]
                conf_int = None
        else:
            predicted = self._predict_ar(all_data)[len(self.training_data):]
            conf_int = None

        # Compute residuals
        residuals = validation_data - predicted
        self._residuals = residuals.tolist()
        self._residual_mean = float(np.mean(residuals))
        self._residual_variance = float(np.var(residuals))

        # Update threshold based on validation residuals
        if len(residuals) > 0:
            residual_std = np.std(residuals)
            if residual_std > 0:
                # Use validation data to refine threshold
                # Default to 3 sigma, but adjust if validation shows different distribution
                self.threshold = self.config.threshold * residual_std
                self.residual_std = residual_std
                logger.info(f"Calibrated threshold to {self.threshold:.4f} (residual_std={residual_std:.4f})")

    def predict(self, observation: float, timestamp: Optional[datetime] = None) -> ARIMAPrediction:
        """Make one-step-ahead prediction for new observation.

        Args:
            observation: New observation value
            timestamp: Optional timestamp for the observation

        Returns:
            ARIMAPrediction with prediction details
        """
        if timestamp is None:
            timestamp = datetime.now()

        if not self.is_fitted:
            # Return naive prediction if not fitted
            if len(self.training_data) > 0:
                pred_value = float(np.mean(self.training_data))
            else:
                pred_value = float(observation)
            residual = observation - pred_value
            score = abs(residual)
            is_anomaly = score > self.threshold

            pred = ARIMAPrediction(
                timestamp=timestamp,
                observed_value=observation,
                predicted_value=pred_value,
                residual=residual,
                anomaly_score=score,
                is_anomaly=is_anomaly
            )
            self.prediction_history.append(pred)
            return pred

        # Make prediction based on model type
        if HAS_STATSMODELS and self.model is not None:
            try:
                # Update model with new observation and predict
                self.model_fit = self.model_fit.append([observation])
                forecast = self.model_fit.get_forecast(steps=1)
                pred_value = float(forecast.predicted_mean.values[0])
                conf_int = forecast.conf_int(alpha=0.05)
                conf_lower = float(conf_int.iloc[0, 0])
                conf_upper = float(conf_int.iloc[0, 1])
            except Exception as e:
                logger.warning(f"statsmodels prediction failed: {e}, using simple AR")
                pred_value, conf_lower, conf_upper = self._predict_simple(observation)
        else:
            pred_value, conf_lower, conf_upper = self._predict_simple(observation)

        # Compute residual and anomaly score
        residual = observation - pred_value
        anomaly_score = abs(residual) / max(self.residual_std, 1e-6)
        is_anomaly = anomaly_score > self.threshold

        # Update residual statistics
        self._update_residual_stats(residual)

        pred = ARIMAPrediction(
            timestamp=timestamp,
            observed_value=observation,
            predicted_value=pred_value,
            residual=residual,
            anomaly_score=anomaly_score,
            is_anomaly=is_anomaly,
            confidence_interval_lower=conf_lower,
            confidence_interval_upper=conf_upper,
            model_params=self._get_model_params()
        )
        self.prediction_history.append(pred)
        return pred

    def _predict_simple(self, observation: float) -> Tuple[float, Optional[float], Optional[float]]:
        """Make prediction using simple AR model."""
        if len(self._simple_ar_coeffs) == 0:
            return self._simple_ar_intercept, None, None

        # Use last p observations
        p = len(self._simple_ar_coeffs)
        recent = self.training_data[-p:] if len(self.training_data) >= p else self.training_data

        pred = self._simple_ar_intercept
        for j, coeff in enumerate(self._simple_ar_coeffs):
            if j < len(recent):
                pred += coeff * recent[-(j+1)]

        # Simple confidence interval based on residual std
        conf_margin = 1.96 * self.residual_std if self.residual_std else 0.0
        return pred, pred - conf_margin, pred + conf_margin

    def _update_residual_stats(self, residual: float) -> None:
        """Update running residual statistics for online threshold adjustment."""
        n = len(self._residuals) + 1
        delta = residual - self._residual_mean
        self._residual_mean += delta / n
        self._residual_variance += delta * (residual - self._residual_mean)
        self._residuals.append(residual)

    def _get_model_params(self) -> Dict[str, Any]:
        """Get current model parameters for inspection."""
        params = {
            'config': self.config.to_dict(),
            'is_fitted': self.is_fitted,
            'training_data_length': len(self.training_data),
            'residual_std': float(self.residual_std) if self.residual_std else None,
            'threshold': float(self.threshold),
            'residual_mean': float(self._residual_mean),
            'residual_variance': float(self._residual_variance),
            'prediction_count': len(self.prediction_history)
        }

        if hasattr(self, '_simple_ar_coeffs'):
            params['ar_coefficients'] = self._simple_ar_coeffs
            params['intercept'] = self._simple_ar_intercept

        if HAS_STATSMODELS and self.model is not None and hasattr(self, 'model_fit'):
            try:
                params['arima_params'] = self.model_fit.params.tolist()
            except Exception:
                pass

        return params

    def get_anomaly_scores(self, observations: Union[List[float], np.ndarray],
                           timestamps: Optional[List[datetime]] = None) -> List[ARIMAPrediction]:
        """Generate anomaly scores for a batch of observations.

        Args:
            observations: Sequence of observations to score
            timestamps: Optional timestamps for each observation

        Returns:
            List of ARIMAPrediction objects
        """
        observations = np.asarray(observations, dtype=np.float64)
        timestamps = timestamps or [datetime.now()] * len(observations)

        predictions = []
        for i, obs in enumerate(observations):
            ts = timestamps[i] if i < len(timestamps) else datetime.now()
            pred = self.predict(obs, timestamp=ts)
            predictions.append(pred)

        return predictions

    def save_checkpoint(self, path: Union[str, Path]) -> None:
        """Save model checkpoint to file.

        Args:
            path: Path to save checkpoint
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        checkpoint = {
            'config': self.config.to_dict(),
            'training_data': self.training_data,
            'residual_std': float(self.residual_std) if self.residual_std else None,
            'threshold': float(self.threshold),
            'is_fitted': self.is_fitted,
            'prediction_count': len(self.prediction_history),
            'checkpoint_time': datetime.now().isoformat()
        }

        if hasattr(self, '_simple_ar_coeffs'):
            checkpoint['ar_coefficients'] = self._simple_ar_coeffs
            checkpoint['intercept'] = self._simple_ar_intercept

        if HAS_STATSMODELS and self.model is not None and hasattr(self, 'model_fit'):
            try:
                checkpoint['model_state'] = self.model_fit.params.tolist()
            except Exception:
                pass

        with open(path, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        logger.info(f"Checkpoint saved to {path}")

    @classmethod
    def load_checkpoint(cls, path: Union[str, Path]) -> 'ARIMABaseline':
        """Load model checkpoint from file.

        Args:
            path: Path to load checkpoint from

        Returns:
            ARIMABaseline instance
        """
        path = Path(path)
        with open(path, 'r') as f:
            checkpoint = json.load(f)

        config = ARIMAConfig.from_dict(checkpoint['config'])
        model = cls(config)

        model.training_data = checkpoint['training_data']
        model.residual_std = checkpoint.get('residual_std')
        model.threshold = checkpoint.get('threshold', model.threshold)
        model.is_fitted = checkpoint.get('is_fitted', False)

        if 'ar_coefficients' in checkpoint:
            model._simple_ar_coeffs = checkpoint['ar_coefficients']
            model._simple_ar_intercept = checkpoint.get('intercept', 0.0)

        return model


def create_baseline(config: Optional[ARIMAConfig] = None) -> ARIMABaseline:
    """Factory function to create ARIMA baseline instance.

    Args:
        config: ARIMAConfig instance. Uses defaults if None.

    Returns:
        ARIMABaseline instance
    """
    return ARIMABaseline(config)


def main():
    """Main entry point for ARIMA baseline testing.

    This function:
    1. Creates synthetic test data with known anomalies
    2. Fits ARIMA model on training data
    3. Generates predictions and anomaly scores
    4. Outputs summary statistics

    Can be run standalone for testing:
        python -m code.src.baselines.arima
    """
    logger.info("ARIMA Baseline Test - Starting")

    # Generate synthetic test data
    np.random.seed(42)
    n_points = 500
    n_anomalies = 20

    # Create base signal with trend and seasonality
    t = np.arange(n_points)
    trend = 0.01 * t
    seasonality = 2 * np.sin(2 * np.pi * t / 50)
    noise = np.random.normal(0, 0.5, n_points)
    base_signal = 10 + trend + seasonality + noise

    # Inject anomalies
    anomaly_indices = np.random.choice(n_points, n_anomalies, replace=False)
    anomaly_signal = base_signal.copy()
    for idx in anomaly_indices:
        # Inject point anomalies (sudden spikes)
        anomaly_signal[idx] += np.random.choice([-1, 1]) * np.random.uniform(5, 10)

    # Split into train/validation/test
    train_size = 200
    val_size = 100
    test_size = n_points - train_size - val_size

    train_data = anomaly_signal[:train_size]
    val_data = anomaly_signal[train_size:train_size + val_size]
    test_data = anomaly_signal[train_size + val_size:]

    test_labels = np.zeros(len(test_data), dtype=bool)
    test_anomaly_indices = anomaly_indices[(anomaly_indices >= train_size + val_size) - (train_size + val_size)]

    # Create and fit model
    config = ARIMAConfig(
        order=(2, 1, 1),
        threshold=3.0,
        training_window=100,
        validation_window=50,
        random_state=42
    )

    baseline = create_baseline(config)
    baseline.fit(train_data, validation_data=val_data)

    # Generate predictions on test data
    predictions = baseline.get_anomaly_scores(test_data)

    # Compute evaluation metrics
    predicted_anomalies = np.array([p.is_anomaly for p in predictions])
    true_anomalies = np.zeros(len(test_data), dtype=bool)
    for idx in test_anomaly_indices:
        if idx < len(test_data):
            true_anomalies[idx] = True

    # Calculate metrics
    tp = np.sum(predicted_anomalies & true_anomalies)
    fp = np.sum(predicted_anomalies & ~true_anomalies)
    fn = np.sum(~predicted_anomalies & true_anomalies)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    # Output results
    print("\n" + "=" * 60)
    print("ARIMA Baseline Results")
    print("=" * 60)
    print(f"Training data points: {len(train_data)}")
    print(f"Validation data points: {len(val_data)}")
    print(f"Test data points: {len(test_data)}")
    print(f"True anomalies in test: {np.sum(true_anomalies)}")
    print(f"Predicted anomalies: {np.sum(predicted_anomalies)}")
    print(f"True Positives: {tp}")
    print(f"False Positives: {fp}")
    print(f"False Negatives: {fn}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall: {recall:.4f}")
    print(f"F1-Score: {f1:.4f}")
    print(f"Residual Std: {baseline.residual_std:.4f}")
    print(f"Threshold: {baseline.threshold:.4f}")
    print("=" * 60)

    # Save sample predictions
    output_dir = Path("data/processed/results")
    output_dir.mkdir(parents=True, exist_ok=True)

    predictions_path = output_dir / "arima_predictions.json"
    predictions_data = [p.to_dict() for p in predictions]
    with open(predictions_path, 'w') as f:
        json.dump(predictions_data, f, indent=2)

    logger.info(f"Predictions saved to {predictions_path}")
    logger.info("ARIMA Baseline Test - Complete")

    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'n_predictions': len(predictions),
        'n_anomalies_detected': int(np.sum(predicted_anomalies))
    }


if __name__ == '__main__':
    main()
