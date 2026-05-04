"""
Moving Average with Z-Score Baseline for Anomaly Detection in Time Series.

This module implements a simple yet effective baseline that uses
rolling window moving averages and z-scores to detect anomalies.
An observation is flagged as anomalous if its z-score exceeds a
configurable threshold.

US2 Acceptance Scenario 1: Can be tested by running on a single UCI
dataset and generating precision-recall curves with F1-score measurements.

API Surface (per plan.md):
- MovingAverageConfig: Configuration dataclass
- MovingAveragePrediction: Prediction output dataclass
- MovingAverageState: Internal state for streaming updates
- MovingAverageBaseline: Main baseline model class
- create_baseline: Factory function
- main: CLI entry point
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path
import sys
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MovingAverageConfig:
    """Configuration for Moving Average Z-Score baseline."""
    window_size: int = 50  # Number of observations for rolling average
    z_threshold: float = 3.0  # Z-score threshold for anomaly flagging
    min_window_size: int = 10  # Minimum observations before scoring starts
    handle_missing: str = "skip"  # "skip", "impute_mean", "impute_zero"
    min_variance: float = 1e-6  # Minimum variance to avoid division by zero
    random_seed: Optional[int] = None  # For reproducibility

    def __post_init__(self):
        if self.window_size < 1:
            raise ValueError("window_size must be >= 1")
        if self.z_threshold < 0:
            raise ValueError("z_threshold must be >= 0")
        if self.min_window_size < 1:
            raise ValueError("min_window_size must be >= 1")
        if self.min_variance < 0:
            raise ValueError("min_variance must be >= 0")


@dataclass
class MovingAveragePrediction:
    """Prediction output from Moving Average baseline."""
    timestamp: datetime
    observation: float
    moving_average: float
    rolling_std: float
    z_score: float
    is_anomaly: bool
    threshold_used: float
    component_count: int  # Number of observations in window

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'observation': float(self.observation),
            'moving_average': float(self.moving_average),
            'rolling_std': float(self.rolling_std),
            'z_score': float(self.z_score),
            'is_anomaly': bool(self.is_anomaly),
            'threshold_used': float(self.threshold_used),
            'component_count': int(self.component_count)
        }


@dataclass
class MovingAverageState:
    """Internal state for streaming moving average computation."""
    window: List[float] = field(default_factory=list)
    sum_window: float = 0.0
    sum_sq_window: float = 0.0
    total_count: int = 0
    missing_count: int = 0
    last_update: Optional[datetime] = None

    @property
    def mean(self) -> float:
        """Compute current moving average."""
        if len(self.window) == 0:
            return 0.0
        return self.sum_window / len(self.window)

    @property
    def std(self) -> float:
        """Compute current rolling standard deviation."""
        n = len(self.window)
        if n < 2:
            return 0.0
        variance = (self.sum_sq_window / n) - (self.mean ** 2)
        # Ensure non-negative variance (numerical stability)
        variance = max(variance, 0.0)
        return np.sqrt(variance)

    def update(self, value: float) -> None:
        """Add a new value to the rolling window."""
        self.window.append(value)
        self.sum_window += value
        self.sum_sq_window += value ** 2
        self.total_count += 1
        self.last_update = datetime.now()

        # Evict oldest value if window is full
        if len(self.window) > self.config.window_size:
            old_value = self.window.pop(0)
            self.sum_window -= old_value
            self.sum_sq_window -= old_value ** 2

    def impute_missing(self) -> float:
        """Handle missing value based on config strategy."""
        if self.handle_missing == "skip":
            return np.nan
        elif self.handle_missing == "impute_mean":
            return self.mean if len(self.window) > 0 else 0.0
        elif self.handle_missing == "impute_zero":
            return 0.0
        else:
            logger.warning(f"Unknown handle_missing strategy: {self.handle_missing}, using mean")
            return self.mean if len(self.window) > 0 else 0.0

    @property
    def config(self) -> MovingAverageConfig:
        """Get config reference (stored externally for state persistence)."""
        return self._config

    @config.setter
    def config(self, value: MovingAverageConfig):
        self._config = value

    @property
    def handle_missing(self) -> str:
        return self.config.handle_missing

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state for checkpointing."""
        return {
            'window': self.window,
            'sum_window': self.sum_window,
            'sum_sq_window': self.sum_sq_window,
            'total_count': self.total_count,
            'missing_count': self.missing_count,
            'last_update': self.last_update.isoformat() if self.last_update else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], config: MovingAverageConfig) -> 'MovingAverageState':
        """Deserialize state from checkpoint."""
        state = cls()
        state.window = data.get('window', [])
        state.sum_window = data.get('sum_window', 0.0)
        state.sum_sq_window = data.get('sum_sq_window', 0.0)
        state.total_count = data.get('total_count', 0)
        state.missing_count = data.get('missing_count', 0)
        if data.get('last_update'):
            state.last_update = datetime.fromisoformat(data['last_update'])
        state.config = config
        return state


class MovingAverageBaseline:
    """
    Moving Average with Z-Score Baseline for Anomaly Detection.

    This baseline computes a rolling moving average and standard deviation
    over a configurable window, then flags observations as anomalies when
    their z-score exceeds a threshold.

    Streaming: Processes observations one at a time, maintaining only
    the current window in memory (O(window_size) memory complexity).

    US2 Acceptance: Produces anomaly scores that can be compared against
    DPGMM on the same datasets with F1-score validation.
    """

    def __init__(self, config: MovingAverageConfig):
        """
        Initialize the Moving Average baseline.

        Args:
            config: Configuration parameters for the baseline
        """
        self.config = config
        self.state = MovingAverageState()
        self.state.config = config

        if config.random_seed is not None:
            np.random.seed(config.random_seed)

        logger.info(f"Initialized MovingAverageBaseline with window_size={config.window_size}, "
                   f"z_threshold={config.z_threshold}")

    def update(self, observation: float, timestamp: Optional[datetime] = None) -> None:
        """
        Update the internal state with a new observation.

        Args:
            observation: The new observation value
            timestamp: Optional timestamp for the observation
        """
        if observation is None or (isinstance(observation, float) and np.isnan(observation)):
            self.state.missing_count += 1
            if self.config.handle_missing == "skip":
                return  # Skip missing values without updating
            else:
                # Impute missing value
                observation = self.state.impute_missing()

        self.state.update(observation)

    def score(self, observation: float, timestamp: Optional[datetime] = None) -> MovingAveragePrediction:
        """
        Compute anomaly score for an observation.

        Args:
            observation: The observation to score
            timestamp: Optional timestamp for the observation

        Returns:
            MovingAveragePrediction with z-score and anomaly flag
        """
        ts = timestamp or datetime.now()

        # Compute z-score
        if self.state.total_count < self.config.min_window_size:
            # Not enough data yet, return non-anomaly
            z_score = 0.0
            is_anomaly = False
        else:
            std = self.state.std
            # Handle low variance case
            if std < self.config.min_variance:
                std = self.config.min_variance

            z_score = abs(observation - self.state.mean) / std
            is_anomaly = z_score > self.config.z_threshold

        return MovingAveragePrediction(
            timestamp=ts,
            observation=observation,
            moving_average=self.state.mean,
            rolling_std=self.state.std,
            z_score=z_score,
            is_anomaly=is_anomaly,
            threshold_used=self.config.z_threshold,
            component_count=len(self.state.window)
        )

    def score_batch(self, observations: List[float],
                   timestamps: Optional[List[datetime]] = None) -> List[MovingAveragePrediction]:
        """
        Score a batch of observations.

        Args:
            observations: List of observation values
            timestamps: Optional list of timestamps

        Returns:
            List of MovingAveragePrediction objects
        """
        predictions = []
        ts_list = timestamps or [datetime.now()] * len(observations)

        for obs, ts in zip(observations, ts_list):
            pred = self.score(obs, ts)
            predictions.append(pred)
            self.update(obs, ts)

        return predictions

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics about the model state.

        Returns:
            Dictionary with model statistics
        """
        return {
            'config': {
                'window_size': self.config.window_size,
                'z_threshold': self.config.z_threshold,
                'min_window_size': self.config.min_window_size,
                'handle_missing': self.config.handle_missing,
                'min_variance': self.config.min_variance
            },
            'state': {
                'total_observations': self.state.total_count,
                'missing_observations': self.state.missing_count,
                'current_window_size': len(self.state.window),
                'current_mean': self.state.mean,
                'current_std': self.state.std,
                'last_update': self.state.last_update.isoformat() if self.state.last_update else None
            }
        }

    def save_checkpoint(self, path: Path) -> None:
        """
        Save model state to checkpoint file.

        Args:
            path: Path to save checkpoint
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint = {
            'config': {
                'window_size': self.config.window_size,
                'z_threshold': self.config.z_threshold,
                'min_window_size': self.config.min_window_size,
                'handle_missing': self.config.handle_missing,
                'min_variance': self.config.min_variance,
                'random_seed': self.config.random_seed
            },
            'state': self.state.to_dict()
        }
        with open(path, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        logger.info(f"Saved checkpoint to {path}")

    @classmethod
    def load_checkpoint(cls, path: Path) -> 'MovingAverageBaseline':
        """
        Load model from checkpoint file.

        Args:
            path: Path to checkpoint file

        Returns:
            Restored MovingAverageBaseline instance
        """
        with open(path, 'r') as f:
            checkpoint = json.load(f)

        config = MovingAverageConfig(**checkpoint['config'])
        model = cls(config)
        model.state = MovingAverageState.from_dict(checkpoint['state'], config)
        logger.info(f"Loaded checkpoint from {path}")
        return model


def create_baseline(config: Optional[MovingAverageConfig] = None) -> MovingAverageBaseline:
    """
    Factory function to create a Moving Average baseline.

    Args:
        config: Optional configuration (uses defaults if None)

    Returns:
        Configured MovingAverageBaseline instance
    """
    if config is None:
        config = MovingAverageConfig()
    return MovingAverageBaseline(config)


def main():
    """CLI entry point for testing Moving Average baseline."""
    import argparse

    parser = argparse.ArgumentParser(description='Moving Average Z-Score Baseline')
    parser.add_argument('--window-size', type=int, default=50, help='Rolling window size')
    parser.add_argument('--z-threshold', type=float, default=3.0, help='Z-score threshold')
    parser.add_argument('--min-window', type=int, default=10, help='Minimum window before scoring')
    parser.add_argument('--seed', type=int, default=None, help='Random seed')
    parser.add_argument('--output', type=str, default=None, help='Output JSON file')
    parser.add_argument('--test', action='store_true', help='Run self-test')

    args = parser.parse_args()

    if args.test:
        # Self-test with synthetic data
        logger.info("Running self-test...")
        np.random.seed(42)

        # Generate synthetic time series with anomalies
        n_points = 1000
        base_signal = np.sin(np.linspace(0, 10 * np.pi, n_points))
        noise = np.random.normal(0, 0.5, n_points)
        observations = base_signal + noise

        # Inject anomalies at known positions
        anomaly_positions = [100, 300, 500, 700, 900]
        anomaly_values = [observations[i] + 5.0 for i in anomaly_positions]
        for pos, val in zip(anomaly_positions, anomaly_values):
            observations[pos] = val

        # Create baseline
        config = MovingAverageConfig(
            window_size=args.window_size,
            z_threshold=args.z_threshold,
            min_window_size=args.min_window,
            random_seed=args.seed
        )
        model = create_baseline(config)

        # Score all observations
        predictions = []
        for i, obs in enumerate(observations):
            pred = model.score(obs)
            predictions.append(pred)

            # Log detected anomalies
            if pred.is_anomaly:
                logger.info(f"Anomaly detected at index {i}: obs={obs:.2f}, "
                           f"z_score={pred.z_score:.2f}, mean={pred.moving_average:.2f}")

        # Compute detection metrics
        detected_anomalies = [i for i, p in enumerate(predictions) if p.is_anomaly]
        true_positives = sum(1 for pos in anomaly_positions if pos in detected_anomalies)
        false_positives = sum(1 for i in detected_anomalies if i not in anomaly_positions)

        logger.info(f"\nSelf-test Results:")
        logger.info(f"  Total observations: {len(observations)}")
        logger.info(f"  True anomalies injected: {len(anomaly_positions)}")
        logger.info(f"  Anomalies detected: {len(detected_anomalies)}")
        logger.info(f"  True positives: {true_positives}")
        logger.info(f"  False positives: {false_positives}")

        # Save predictions if requested
        if args.output:
            output_data = {
                'config': model.get_summary()['config'],
                'state': model.get_summary()['state'],
                'predictions': [p.to_dict() for p in predictions],
                'test_results': {
                    'true_positives': true_positives,
                    'false_positives': false_positives,
                    'anomaly_positions': anomaly_positions,
                    'detected_anomalies': detected_anomalies
                }
            }
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
            logger.info(f"Saved predictions to {args.output}")

        logger.info("Self-test completed successfully!")
        return 0

    return 0


if __name__ == '__main__':
    sys.exit(main())
