"""
ARIMA Baseline for Time Series Anomaly Detection.

Implements ARIMA-based anomaly detection using residual analysis.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, Union
from datetime import datetime
from pathlib import Path
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ARIMAConfig:
    """Configuration for ARIMA baseline model."""
    order_p: int = 1
    order_d: int = 1
    order_q: int = 1
    seasonal_period: int = 1
    anomaly_threshold: float = 2.0
    min_train_samples: int = 10
    max_forecast_horizon: int = 1

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.order_p < 0 or self.order_d < 0 or self.order_q < 0:
            raise ValueError("ARIMA order parameters must be non-negative")
        if self.anomaly_threshold <= 0:
            raise ValueError("anomaly_threshold must be positive")
        if self.min_train_samples < 1:
            raise ValueError("min_train_samples must be at least 1")


@dataclass
class ARIMAPrediction:
    """Prediction result from ARIMA model."""
    timestamp: str
    observed: float
    predicted: float
    residual: float
    is_anomaly: bool
    anomaly_score: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert prediction to dictionary."""
        return {
            "timestamp": self.timestamp,
            "observed": self.observed,
            "predicted": self.predicted,
            "residual": self.residual,
            "is_anomaly": self.is_anomaly,
            "anomaly_score": self.anomaly_score
        }


class ARIMABaseline:
    """
    ARIMA-based anomaly detection baseline.

    Uses residual analysis to identify anomalies.
    """

    def __init__(self, config: Optional[ARIMAConfig] = None) -> None:
        """Initialize ARIMA baseline with configuration."""
        self.config = config or ARIMAConfig()
        self._residuals: List[float] = []
        self._residual_std: float = 1.0
        self._residual_mean: float = 0.0
        self._trained: bool = False

    def train(self, time_series: np.ndarray) -> None:
        """
Train ARIMA model on time series data.

Args:
    time_series: Array of time series values
"""
        if len(time_series) < self.config.min_train_samples:
            raise ValueError(
                f"Time series has {len(time_series)} samples, "
                f"minimum required is {self.config.min_train_samples}"
            )

        logger.info(f"Training ARIMA({self.config.order_p},"
                  f"{self.config.order_d},{self.config.order_q})")

        # Simulate ARIMA fitting using differencing and moving average
        # In production, this would use statsmodels.tsa.arima_model

        # Compute residuals (simplified: difference from rolling mean)
        window = max(5, len(time_series) // 10)
        rolling_mean = self._compute_rolling_mean(time_series, window)

        # First n points don't have rolling mean
        residuals = []
        for i in range(window, len(time_series)):
            residual = float(time_series[i] - rolling_mean[i])
            residuals.append(residual)

        self._residuals = residuals
        self._residual_mean = float(np.mean(residuals))
        self._residual_std = float(np.std(residuals) + 1e-10)

        self._trained = True
        logger.info(f"Training complete. Residual mean={self._residual_mean:.4f}, "
                  f"std={self._residual_std:.4f}")

    def _compute_rolling_mean(self, data: np.ndarray,
                             window: int) -> np.ndarray:
        """Compute rolling mean with given window size."""
        result = np.zeros_like(data, dtype=float)
        for i in range(len(data)):
            start = max(0, i - window)
            result[i] = np.mean(data[start:i + 1])
        return result

    def predict(self, observation: float,
               timestamp: Optional[str] = None) -> ARIMAPrediction:
        """
Predict anomaly status for a single observation.

Args:
    observation: Single time series value
    timestamp: Optional timestamp for the observation

Returns:
    ARIMAPrediction object with anomaly assessment
"""
        if not self._trained:
            raise RuntimeError("Model must be trained before prediction")

        # Simple residual-based anomaly detection
        residual = observation - self._residual_mean
        z_score = abs(residual) / self._residual_std

        is_anomaly = z_score > self.config.anomaly_threshold
        anomaly_score = float(z_score)

        ts = timestamp or datetime.now().isoformat()

        return ARIMAPrediction(
            timestamp=ts,
            observed=observation,
            predicted=self._residual_mean,
            residual=residual,
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score
        )

    def evaluate(self, time_series: np.ndarray,
                ground_truth: Optional[np.ndarray] = None) -> Dict[str, float]:
        """
Evaluate model performance on time series.

Args:
    time_series: Time series to evaluate
    ground_truth: Optional ground truth anomaly labels

Returns:
    Dictionary of evaluation metrics
"""
        if not self._trained:
            raise RuntimeError("Model must be trained before evaluation")

        predictions = []
        for obs in time_series:
            pred = self.predict(obs)
            predictions.append(pred)

        results = {
            "n_predictions": len(predictions),
            "n_anomalies_detected": sum(1 for p in predictions if p.is_anomaly),
            "anomaly_rate": float(
                sum(1 for p in predictions if p.is_anomaly) / len(predictions)
            )
        }

        if ground_truth is not None:
            y_pred = [1 if p.is_anomaly else 0 for p in predictions]
            y_true = ground_truth.astype(int)

            # Compute basic metrics
            tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
            fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
            fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

            results["precision"] = precision
            results["recall"] = recall
            results["f1_score"] = f1

        return results


def create_baseline(config: Optional[ARIMAConfig] = None) -> ARIMABaseline:
    """
Factory function to create ARIMA baseline.

Args:
    config: Optional configuration

Returns:
    Configured ARIMABaseline instance
"""
    return ARIMABaseline(config)


def main() -> None:
    """Main entry point for ARIMA baseline testing."""
    logger.info("ARIMA Baseline Test")

    # Create configuration
    config = ARIMAConfig(
        order_p=1,
        order_d=1,
        order_q=1,
        anomaly_threshold=2.5
    )

    # Create and train model
    model = create_baseline(config)

    # Generate synthetic time series
    np.random.seed(42)
    time_series = np.sin(np.linspace(0, 10, 100)) + np.random.randn(100) * 0.5

    model.train(time_series[:80])

    # Evaluate on test set
    results = model.evaluate(time_series[80:], None)

    logger.info(f"Predictions: {results['n_predictions']}")
    logger.info(f"Anomalies detected: {results['n_anomalies_detected']}")
    logger.info(f"Anomaly rate: {results['anomaly_rate']:.4f}")

    logger.info("Test completed successfully")


if __name__ == "__main__":
    main()
