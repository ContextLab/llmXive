"""
Moving Average with Z-Score Baseline for Anomaly Detection.

Implements simple moving average baseline with z-score anomaly scoring.
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MovingAverageConfig:
    """Configuration for moving average baseline model."""
    window_size: int = 10
    z_score_threshold: float = 2.0
    min_samples: int = 5
    min_variance: float = 1e-6

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.window_size < 1:
            raise ValueError("window_size must be at least 1")
        if self.z_score_threshold <= 0:
            raise ValueError("z_score_threshold must be positive")
        if self.min_samples < 1:
            raise ValueError("min_samples must be at least 1")
        if self.min_variance <= 0:
            raise ValueError("min_variance must be positive")


@dataclass
class MovingAveragePrediction:
    """Prediction result from moving average model."""
    timestamp: str
    observed: float
    moving_average: float
    standard_deviation: float
    z_score: float
    is_anomaly: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert prediction to dictionary."""
        return {
            "timestamp": self.timestamp,
            "observed": self.observed,
            "moving_average": self.moving_average,
            "standard_deviation": self.standard_deviation,
            "z_score": self.z_score,
            "is_anomaly": self.is_anomaly
        }


@dataclass
class MovingAverageState:
    """Internal state for streaming moving average computation."""
    values: List[float] = field(default_factory=list)
    sum_values: float = 0.0
    sum_sq_values: float = 0.0
    n_observations: int = 0

    def update(self, value: float) -> None:
        """Update state with new observation."""
        self.values.append(value)
        self.sum_values += value
        self.sum_sq_values += value ** 2
        self.n_observations += 1

        # Maintain window size
        if len(self.values) > self.window_size:
            old_value = self.values.pop(0)
            self.sum_values -= old_value
            self.sum_sq_values -= old_value ** 2

    @property
    def window_size(self) -> int:
        """Default window size."""
        return 10

    def get_mean(self) -> float:
        """Get current moving average."""
        if len(self.values) == 0:
            return 0.0
        return self.sum_values / len(self.values)

    def get_std(self) -> float:
        """Get current standard deviation."""
        n = len(self.values)
        if n < 2:
            return 1.0
        mean = self.get_mean()
        variance = (self.sum_sq_values / n) - (mean ** 2)
        return max(np.sqrt(max(variance, 0.0)), 1e-6)


class MovingAverageBaseline:
    """
    Moving average with z-score anomaly detection baseline.

    Uses rolling window statistics to compute anomaly scores.
    """

    def __init__(self, config: Optional[MovingAverageConfig] = None) -> None:
        """Initialize moving average baseline with configuration."""
        self.config = config or MovingAverageConfig()
        self._state = MovingAverageState()
        self._predictions: List[MovingAveragePrediction] = []

    def _get_window_size(self) -> int:
        """Get window size from state or config."""
        return self.config.window_size

    def process(self, observation: float,
               timestamp: Optional[str] = None) -> MovingAveragePrediction:
        """
Process a single observation and compute anomaly score.

Args:
    observation: Single time series value
    timestamp: Optional timestamp for the observation

Returns:
    MovingAveragePrediction object with anomaly assessment
"""
        ts = timestamp or datetime.now().isoformat()

        # Get current statistics before updating
        if len(self._state.values) < self.config.min_samples:
            # Not enough samples yet, just update state
            self._state.update(observation)
            return MovingAveragePrediction(
                timestamp=ts,
                observed=observation,
                moving_average=observation,
                standard_deviation=0.0,
                z_score=0.0,
                is_anomaly=False
            )

        moving_avg = self._state.get_mean()
        std_dev = self._state.get_std()

        # Compute z-score
        variance = std_dev ** 2
        if variance < self.config.min_variance:
            z_score = 0.0
        else:
            z_score = abs(observation - moving_avg) / std_dev

        is_anomaly = z_score > self.config.z_score_threshold

        prediction = MovingAveragePrediction(
            timestamp=ts,
            observed=observation,
            moving_average=moving_avg,
            standard_deviation=std_dev,
            z_score=z_score,
            is_anomaly=is_anomaly
        )

        self._predictions.append(prediction)
        self._state.update(observation)

        return prediction

    def process_batch(self, observations: np.ndarray,
                    timestamps: Optional[List[str]] = None) -> List[MovingAveragePrediction]:
        """
Process a batch of observations.

Args:
    observations: Array of time series values
    timestamps: Optional list of timestamps

Returns:
    List of MovingAveragePrediction objects
"""
        if timestamps is None:
            timestamps = [datetime.now().isoformat()] * len(observations)

        predictions = []
        for i, obs in enumerate(observations):
            pred = self.process(float(obs), timestamps[i])
            predictions.append(pred)

        return predictions

    def get_predictions(self) -> List[MovingAveragePrediction]:
        """Return all stored predictions."""
        return self._predictions.copy()

    def reset(self) -> None:
        """Reset model state for fresh processing."""
        self._state = MovingAverageState()
        self._predictions = []


def create_baseline(config: Optional[MovingAverageConfig] = None) -> MovingAverageBaseline:
    """
Factory function to create moving average baseline.

Args:
    config: Optional configuration

Returns:
    Configured MovingAverageBaseline instance
"""
    return MovingAverageBaseline(config)


def main() -> None:
    """Main entry point for moving average baseline testing."""
    logger.info("Moving Average Baseline Test")

    # Create configuration
    config = MovingAverageConfig(
        window_size=10,
        z_score_threshold=2.5
    )

    # Create and run model
    model = create_baseline(config)

    # Generate synthetic time series with anomalies
    np.random.seed(42)
    time_series = np.sin(np.linspace(0, 10, 100)) + np.random.randn(100) * 0.3

    # Inject some anomalies
    time_series[30] += 3.0
    time_series[60] += 4.0
    time_series[85] += 3.5

    # Process batch
    predictions = model.process_batch(time_series)

    # Report results
    n_anomalies = sum(1 for p in predictions if p.is_anomaly)
    logger.info(f"Total predictions: {len(predictions)}")
    logger.info(f"Anomalies detected: {n_anomalies}")

    # Print detected anomalies
    for i, pred in enumerate(predictions):
        if pred.is_anomaly:
            logger.info(f"Anomaly at index {i}: z_score={pred.z_score:.2f}")

    logger.info("Test completed successfully")


if __name__ == "__main__":
    main()