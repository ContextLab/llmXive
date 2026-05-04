"""
Threshold Calibration Service for Anomaly Detection

Implements unsupervised threshold calibration using percentile-based methods
and adaptive boundary updates for streaming anomaly detection.
"""

import numpy as np
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple, Union
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ThresholdCalibrationConfig:
    """Configuration for threshold calibration service."""
    percentile: float = 95.0
    min_samples: int = 100
    max_samples: int = 10000
    smoothing_factor: float = 0.1
    min_threshold: float = 0.0
    max_threshold: float = 1000.0
    update_interval: int = 100
    confidence_level: float = 0.95


@dataclass
class ThresholdState:
    """State information for threshold calibration."""
    current_threshold: float = 0.0
    calibration_percentile: float = 95.0
    sample_count: int = 0
    score_history: List[float] = field(default_factory=list)
    last_update_time: Optional[datetime] = None
    calibration_method: str = "percentile"
    statistics: Dict[str, float] = field(default_factory=dict)


@dataclass
class CalibrationResult:
    """Result of threshold calibration."""
    threshold: float
    method: str
    percentile_used: float
    sample_count: int
    statistics: Dict[str, float]
    timestamp: datetime


class ThresholdCalibratorService:
    """
    Service for unsupervised threshold calibration in anomaly detection.

    Implements percentile-based calibration and adaptive boundary updates
    for streaming time-series anomaly detection without labeled data.
    """

    def __init__(self, config: Optional[ThresholdCalibrationConfig] = None):
        """
        Initialize the threshold calibrator service.

        Args:
            config: Calibration configuration. Uses defaults if None.
        """
        self.config = config or ThresholdCalibrationConfig()
        self.state = ThresholdState()
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if not 0 < self.config.percentile < 100:
            raise ValueError(f"Percentile must be between 0 and 100, got {self.config.percentile}")
        if self.config.min_samples <= 0:
            raise ValueError(f"min_samples must be positive, got {self.config.min_samples}")
        if self.config.min_samples > self.config.max_samples:
            raise ValueError(f"min_samples ({self.config.min_samples}) cannot exceed max_samples ({self.config.max_samples})")
        if not 0 <= self.config.smoothing_factor <= 1:
            raise ValueError(f"smoothing_factor must be between 0 and 1, got {self.config.smoothing_factor}")

    def add_observation(self, score: float) -> None:
        """
        Add an anomaly score observation for calibration.

        Args:
            score: Anomaly score from the detection model.
        """
        if not np.isfinite(score):
            logger.warning(f"Ignoring non-finite score: {score}")
            return

        self.state.score_history.append(float(score))
        self.state.sample_count += 1

        # Trim history if exceeds max samples
        if len(self.state.score_history) > self.config.max_samples:
            # Keep most recent samples
            self.state.score_history = self.state.score_history[-self.config.max_samples:]

        # Update threshold periodically
        if self.state.sample_count % self.config.update_interval == 0:
            self._update_threshold()

    def _update_threshold(self) -> None:
        """Update threshold based on current score distribution."""
        if self.state.sample_count < self.config.min_samples:
            logger.debug(f"Insufficient samples for calibration: {self.state.sample_count} < {self.config.min_samples}")
            return

        self._update_percentile_threshold()
        self.state.last_update_time = datetime.now()

    def _update_percentile_threshold(self) -> None:
        """
        Update threshold using percentile-based calibration method.

        Calculates the threshold as the specified percentile of the
        observed anomaly score distribution.
        """
        if len(self.state.score_history) < self.config.min_samples:
            logger.warning(f"Cannot calibrate: only {len(self.state.score_history)} samples available")
            return

        scores = np.array(self.state.score_history, dtype=np.float64)

        # Calculate percentile threshold
        threshold = np.percentile(scores, self.config.percentile)

        # Apply smoothing if enabled
        if self.config.smoothing_factor > 0 and self.state.current_threshold > 0:
            threshold = (
                self.config.smoothing_factor * threshold +
                (1 - self.config.smoothing_factor) * self.state.current_threshold
            )

        # Apply bounds
        threshold = max(self.config.min_threshold, min(self.config.max_threshold, threshold))

        # Update state
        self.state.current_threshold = float(threshold)
        self.state.calibration_percentile = self.config.percentile
        self.state.calibration_method = "percentile"

        # Calculate statistics
        self.state.statistics = {
            "mean": float(np.mean(scores)),
            "std": float(np.std(scores)),
            "min": float(np.min(scores)),
            "max": float(np.max(scores)),
            "median": float(np.median(scores)),
            "percentile_90": float(np.percentile(scores, 90)),
            "percentile_95": float(np.percentile(scores, 95)),
            "percentile_99": float(np.percentile(scores, 99)),
        }

        logger.info(
            f"Threshold updated: {threshold:.4f} (percentile={self.config.percentile}, "
            f"n={len(scores)}, mean={self.state.statistics['mean']:.4f})"
        )

    def get_threshold(self) -> float:
        """
        Get the current calibrated threshold.

        Returns:
            Current threshold value. If insufficient samples, returns 0.0.
        """
        if self.state.sample_count < self.config.min_samples:
            logger.warning(
                f"Returning default threshold (insufficient samples: "
                f"{self.state.sample_count} < {self.config.min_samples})"
            )
            return 0.0

        return self.state.current_threshold

    def is_anomaly(self, score: float) -> bool:
        """
        Determine if a score indicates an anomaly.

        Args:
            score: Anomaly score to evaluate.

        Returns:
            True if score exceeds threshold, False otherwise.
        """
        threshold = self.get_threshold()
        if threshold == 0.0:
            # No calibration yet - assume not anomaly
            return False

        return score > threshold

    def calibrate_from_scores(
        self,
        scores: List[float],
        percentile: Optional[float] = None
    ) -> CalibrationResult:
        """
        Calibrate threshold from a batch of anomaly scores.

        This method performs one-shot calibration from historical scores
        rather than streaming updates.

        Args:
            scores: List of anomaly scores for calibration.
            percentile: Override the configured percentile. Uses config default if None.

        Returns:
            CalibrationResult with threshold and statistics.
        """
        if len(scores) < self.config.min_samples:
            raise ValueError(
                f"Insufficient scores for calibration: {len(scores)} < {self.config.min_samples}"
            )

        scores_array = np.array(scores, dtype=np.float64)
        p = percentile if percentile is not None else self.config.percentile

        # Calculate threshold
        threshold = float(np.percentile(scores_array, p))

        # Apply bounds
        threshold = max(self.config.min_threshold, min(self.config.max_threshold, threshold))

        # Calculate statistics
        statistics = {
            "mean": float(np.mean(scores_array)),
            "std": float(np.std(scores_array)),
            "min": float(np.min(scores_array)),
            "max": float(np.max(scores_array)),
            "median": float(np.median(scores_array)),
            f"percentile_{int(p)}": threshold,
            "percentile_90": float(np.percentile(scores_array, 90)),
            "percentile_95": float(np.percentile(scores_array, 95)),
            "percentile_99": float(np.percentile(scores_array, 99)),
            "skewness": float(self._compute_skewness(scores_array)),
            "kurtosis": float(self._compute_kurtosis(scores_array)),
        }

        result = CalibrationResult(
            threshold=threshold,
            method="percentile",
            percentile_used=p,
            sample_count=len(scores),
            statistics=statistics,
            timestamp=datetime.now()
        )

        # Update service state
        self.state.current_threshold = threshold
        self.state.calibration_percentile = p
        self.state.calibration_method = "percentile"
        self.state.sample_count = len(scores)
        self.state.score_history = list(scores_array[-self.config.max_samples:])
        self.state.statistics = statistics
        self.state.last_update_time = datetime.now()

        logger.info(
            f"Batch calibration complete: threshold={threshold:.4f}, "
            f"percentile={p}, n={len(scores)}"
        )

        return result

    def _compute_skewness(self, data: np.ndarray) -> float:
        """Compute skewness of the score distribution."""
        if len(data) < 3:
            return 0.0
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0.0
        return float(np.mean(((data - mean) / std) ** 3))

    def _compute_kurtosis(self, data: np.ndarray) -> float:
        """Compute kurtosis of the score distribution."""
        if len(data) < 4:
            return 0.0
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0.0
        return float(np.mean(((data - mean) / std) ** 4) - 3)  # Excess kurtosis

    def get_calibration_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current calibration state.

        Returns:
            Dictionary with calibration statistics and state information.
        """
        return {
            "current_threshold": self.state.current_threshold,
            "calibration_method": self.state.calibration_method,
            "calibration_percentile": self.state.calibration_percentile,
            "sample_count": self.state.sample_count,
            "min_samples_required": self.config.min_samples,
            "statistics": self.state.statistics,
            "last_update_time": self.state.last_update_time.isoformat() if self.state.last_update_time else None,
            "config": {
                "percentile": self.config.percentile,
                "min_samples": self.config.min_samples,
                "max_samples": self.config.max_samples,
                "smoothing_factor": self.config.smoothing_factor,
                "min_threshold": self.config.min_threshold,
                "max_threshold": self.config.max_threshold,
                "update_interval": self.config.update_interval,
            }
        }

    def reset(self) -> None:
        """Reset the calibrator state."""
        self.state = ThresholdState()
        logger.info("Threshold calibrator state reset")

    def save_state(self, path: Union[str, Path]) -> None:
        """
        Save calibration state to file.

        Args:
            path: Path to save state file (JSON format).
        """
        import json

        state_dict = {
            "current_threshold": self.state.current_threshold,
            "calibration_percentile": self.state.calibration_percentile,
            "sample_count": self.state.sample_count,
            "score_history": self.state.score_history,
            "last_update_time": self.state.last_update_time.isoformat() if self.state.last_update_time else None,
            "calibration_method": self.state.calibration_method,
            "statistics": self.state.statistics,
        }

        state_path = Path(path)
        state_path.parent.mkdir(parents=True, exist_ok=True)

        with open(state_path, "w") as f:
            json.dump(state_dict, f, indent=2)

        logger.info(f"Calibration state saved to {state_path}")

    def load_state(self, path: Union[str, Path]) -> None:
        """
        Load calibration state from file.

        Args:
            path: Path to load state file (JSON format).
        """
        import json

        state_path = Path(path)
        if not state_path.exists():
            raise FileNotFoundError(f"State file not found: {state_path}")

        with open(state_path, "r") as f:
            state_dict = json.load(f)

        self.state.current_threshold = state_dict.get("current_threshold", 0.0)
        self.state.calibration_percentile = state_dict.get("calibration_percentile", self.config.percentile)
        self.state.sample_count = state_dict.get("sample_count", 0)
        self.state.score_history = state_dict.get("score_history", [])
        self.state.calibration_method = state_dict.get("calibration_method", "percentile")
        self.state.statistics = state_dict.get("statistics", {})

        last_update = state_dict.get("last_update_time")
        if last_update:
            self.state.last_update_time = datetime.fromisoformat(last_update)

        logger.info(f"Calibration state loaded from {state_path}")


def create_calibrator(config: Optional[ThresholdCalibrationConfig] = None) -> ThresholdCalibratorService:
    """
    Factory function to create a threshold calibrator service.

    Args:
        config: Optional configuration. Uses defaults if None.

    Returns:
        Configured ThresholdCalibratorService instance.
    """
    return ThresholdCalibratorService(config=config)


def main() -> None:
    """
    Main entry point for standalone testing of threshold calibration.

    Demonstrates percentile-based calibration on synthetic anomaly scores.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Test threshold calibration service")
    parser.add_argument("--percentile", type=float, default=95.0, help="Calibration percentile")
    parser.add_argument("--min-samples", type=int, default=100, help="Minimum samples for calibration")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    # Set random seed
    np.random.seed(args.seed)

    # Create calibrator
    config = ThresholdCalibrationConfig(
        percentile=args.percentile,
        min_samples=args.min_samples
    )
    calibrator = create_calibrator(config)

    # Generate synthetic anomaly scores (simulating model output)
    # Normal scores follow N(0.3, 0.1), anomalies follow N(0.8, 0.15)
    n_normal = 500
    n_anomalies = 50
    normal_scores = np.random.normal(0.3, 0.1, n_normal)
    anomaly_scores = np.random.normal(0.8, 0.15, n_anomalies)
    all_scores = np.concatenate([normal_scores, anomaly_scores])

    # Shuffle scores
    np.random.shuffle(all_scores)

    print(f"Testing threshold calibration with {len(all_scores)} scores")
    print(f"Configuration: percentile={config.percentile}, min_samples={config.min_samples}")
    print()

    # Add observations incrementally
    for i, score in enumerate(all_scores):
        calibrator.add_observation(score)
        if (i + 1) % 100 == 0:
            summary = calibrator.get_calibration_summary()
            print(f"Sample {i + 1}: threshold={summary['current_threshold']:.4f}, "
                  f"n={summary['sample_count']}")

    # Final calibration
    print()
    print("=" * 60)
    print("FINAL CALIBRATION SUMMARY")
    print("=" * 60)
    summary = calibrator.get_calibration_summary()
    print(f"Threshold: {summary['current_threshold']:.4f}")
    print(f"Method: {summary['calibration_method']}")
    print(f"Percentile: {summary['calibration_percentile']}")
    print(f"Samples: {summary['sample_count']}")
    print()
    print("Statistics:")
    for key, value in summary['statistics'].items():
        print(f"  {key}: {value:.4f}")

    # Test anomaly detection
    print()
    print("ANOMALY DETECTION TEST")
    print("-" * 40)
    test_scores = [0.1, 0.3, 0.5, 0.7, 0.9]
    for score in test_scores:
        is_anom = calibrator.is_anomaly(score)
        status = "ANOMALY" if is_anom else "NORMAL"
        print(f"Score {score:.2f}: {status} (threshold={summary['current_threshold']:.4f})")

    print()
    print("Calibration test completed successfully!")


if __name__ == "__main__":
    main()
