"""
Threshold calibration utilities for anomaly detection.

Implements adaptive threshold computation for unlabeled data using
statistical properties of anomaly score distributions.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ThresholdCalibrationResult:
    """Result of threshold calibration process."""
    threshold: float
    anomaly_rate: float
    score_percentiles: Dict[str, float]
    calibrated_at: str
    num_observations: int
    num_anomalies_detected: int
    decision_boundary: float  # The actual threshold used
    expected_anomaly_bounds: Tuple[float, float]  # (min_expected_rate, max_expected_rate)
    validation_passed: bool  # Whether anomaly rate is within expected bounds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'threshold': self.threshold,
            'anomaly_rate': self.anomaly_rate,
            'score_percentiles': self.score_percentiles,
            'calibrated_at': self.calibrated_at,
            'num_observations': self.num_observations,
            'num_anomalies_detected': self.num_anomalies_detected,
            'decision_boundary': self.decision_boundary,
            'expected_anomaly_bounds': self.expected_anomaly_bounds,
            'validation_passed': self.validation_passed
        }


@dataclass
class ThresholdConfig:
    """Configuration for threshold calibration."""
    percentile: float = 95.0  # Default 95th percentile
    min_anomaly_rate: float = 0.01  # Minimum expected anomaly rate
    max_anomaly_rate: float = 0.10  # Maximum expected anomaly rate
    smoothing_factor: float = 0.1  # For adaptive updates
    min_samples: int = 100  # Minimum samples required for calibration
    confidence_level: float = 0.95  # For confidence intervals

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            'percentile': self.percentile,
            'min_anomaly_rate': self.min_anomaly_rate,
            'max_anomaly_rate': self.max_anomaly_rate,
            'smoothing_factor': self.smoothing_factor,
            'min_samples': self.min_samples,
            'confidence_level': self.confidence_level
        }


class ThresholdCalibrator:
    """
    Adaptive threshold calibrator for unlabeled anomaly detection.
    
    Uses statistical properties of anomaly score distributions to
    compute thresholds without requiring labeled data.
    """

    def __init__(self, config: Optional[ThresholdConfig] = None):
        """
        Initialize the calibrator.
        
        Args:
            config: ThresholdConfig instance, or None for defaults
        """
        self.config = config or ThresholdConfig()
        self._calibrated = False
        self._threshold: Optional[float] = None
        self._score_history: List[float] = []
        self._calibration_result: Optional[ThresholdCalibrationResult] = None

    def calibrate(self, scores: np.ndarray) -> ThresholdCalibrationResult:
        """
        Calibrate threshold from unlabeled anomaly scores.
        
        Args:
            scores: Array of anomaly scores from the model
        
        Returns:
            ThresholdCalibrationResult with computed threshold and metrics
        
        Raises:
            ValueError: If insufficient samples for calibration
        """
        if len(scores) < self.config.min_samples:
            raise ValueError(
                f"Insufficient samples for calibration: "
                f"got {len(scores)}, need {self.config.min_samples}"
            )

        # Convert to numpy array if needed
        scores = np.asarray(scores, dtype=np.float64)

        # Compute score statistics
        percentile_threshold = np.percentile(scores, self.config.percentile)
        
        # Calculate score distribution percentiles
        score_percentiles = {
            'p25': float(np.percentile(scores, 25)),
            'p50': float(np.percentile(scores, 50)),
            'p75': float(np.percentile(scores, 75)),
            'p90': float(np.percentile(scores, 90)),
            'p95': float(np.percentile(scores, 95)),
            'p99': float(np.percentile(scores, 99)),
            'mean': float(np.mean(scores)),
            'std': float(np.std(scores)),
            'min': float(np.min(scores)),
            'max': float(np.max(scores))
        }

        # Determine final threshold
        threshold = percentile_threshold

        # Count anomalies at this threshold
        anomaly_mask = scores >= threshold
        num_anomalies = int(np.sum(anomaly_mask))
        anomaly_rate = num_anomalies / len(scores)

        # Validate anomaly rate is within expected bounds
        validation_passed = (
            self.config.min_anomaly_rate <= anomaly_rate <=
            self.config.max_anomaly_rate
        )

        # Compute expected bounds for anomaly rate
        expected_bounds = (
            self.config.min_anomaly_rate,
            self.config.max_anomaly_rate
        )

        # Create result
        result = ThresholdCalibrationResult(
            threshold=float(threshold),
            anomaly_rate=float(anomaly_rate),
            score_percentiles=score_percentiles,
            calibrated_at=datetime.utcnow().isoformat(),
            num_observations=len(scores),
            num_anomalies_detected=num_anomalies,
            decision_boundary=float(threshold),
            expected_anomaly_bounds=expected_bounds,
            validation_passed=validation_passed
        )

        # Store state
        self._calibrated = True
        self._threshold = threshold
        self._score_history.extend(scores.tolist())
        self._calibration_result = result

        logger.info(
            f"Threshold calibrated: {threshold:.4f}, "
            f"anomaly_rate: {anomaly_rate:.4f}, "
            f"validation: {'PASSED' if validation_passed else 'FAILED'}"
        )

        return result

    def get_threshold(self) -> float:
        """Get the current calibrated threshold."""
        if not self._calibrated:
            raise RuntimeError("Threshold not yet calibrated. Call calibrate() first.")
        return self._threshold

    def compute_expected_bounds(self) -> Tuple[float, float]:
        """
        Compute expected anomaly rate bounds based on configuration.
        
        Returns:
            Tuple of (min_expected_rate, max_expected_rate)
        """
        return (
            self.config.min_anomaly_rate,
            self.config.max_anomaly_rate
        )

    def validate_threshold(self, scores: np.ndarray) -> bool:
        """
        Validate that the current threshold produces reasonable anomaly rates.
        
        Args:
            scores: New scores to validate against
        
        Returns:
            True if anomaly rate is within expected bounds
        """
        if not self._calibrated:
            raise RuntimeError("Threshold not yet calibrated. Call calibrate() first.")

        scores = np.asarray(scores, dtype=np.float64)
        anomaly_mask = scores >= self._threshold
        anomaly_rate = np.sum(anomaly_mask) / len(scores)

        return (
            self.config.min_anomaly_rate <= anomaly_rate <=
            self.config.max_anomaly_rate
        )

    def update_threshold(self, new_threshold: float) -> None:
        """
        Manually update the threshold decision boundary.
        
        Args:
            new_threshold: New threshold value
        """
        self._threshold = new_threshold
        self._calibrated = True
        logger.info(f"Threshold manually updated to: {new_threshold:.4f}")

    def get_decision_boundary(self) -> float:
        """Get the current decision boundary (threshold)."""
        return self.get_threshold()

    def get_calibration_result(self) -> Optional[ThresholdCalibrationResult]:
        """Get the last calibration result."""
        return self._calibration_result


def compute_adaptive_threshold(
    scores: np.ndarray,
    percentile: float = 95.0,
    min_rate: float = 0.01,
    max_rate: float = 0.10
) -> ThresholdCalibrationResult:
    """
    Convenience function to compute adaptive threshold.
    
    Args:
        scores: Array of anomaly scores
        percentile: Percentile to use for threshold (default 95)
        min_rate: Minimum expected anomaly rate
        max_rate: Maximum expected anomaly rate
    
    Returns:
        ThresholdCalibrationResult
    """
    config = ThresholdConfig(
        percentile=percentile,
        min_anomaly_rate=min_rate,
        max_anomaly_rate=max_rate
    )
    calibrator = ThresholdCalibrator(config)
    return calibrator.calibrate(scores)


def validate_anomaly_rate(
    scores: np.ndarray,
    threshold: float,
    min_rate: float = 0.01,
    max_rate: float = 0.10
) -> Tuple[bool, float]:
    """
    Validate that anomaly rate at threshold is within bounds.
    
    Args:
        scores: Array of anomaly scores
        threshold: Threshold to validate
        min_rate: Minimum expected anomaly rate
        max_rate: Maximum expected anomaly rate
    
    Returns:
        Tuple of (validation_passed, actual_rate)
    """
    scores = np.asarray(scores, dtype=np.float64)
    anomaly_mask = scores >= threshold
    anomaly_rate = np.sum(anomaly_mask) / len(scores)

    validation_passed = min_rate <= anomaly_rate <= max_rate
    return validation_passed, anomaly_rate


def save_calibration_result(
    result: ThresholdCalibrationResult,
    output_path: Union[str, Path]
) -> None:
    """
    Save calibration result to JSON file.
    
    Args:
        result: ThresholdCalibrationResult to save
        output_path: Path to save JSON file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)
    
    logger.info(f"Calibration result saved to: {output_path}")


def load_calibration_result(
    input_path: Union[str, Path]
) -> ThresholdCalibrationResult:
    """
    Load calibration result from JSON file.
    
    Args:
        input_path: Path to JSON file
    
    Returns:
        ThresholdCalibrationResult
    """
    input_path = Path(input_path)
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    return ThresholdCalibrationResult(
        threshold=data['threshold'],
        anomaly_rate=data['anomaly_rate'],
        score_percentiles=data['score_percentiles'],
        calibrated_at=data['calibrated_at'],
        num_observations=data['num_observations'],
        num_anomalies_detected=data['num_anomalies_detected'],
        decision_boundary=data['decision_boundary'],
        expected_anomaly_bounds=tuple(data['expected_anomaly_bounds']),
        validation_passed=data['validation_passed']
    )


def main():
    """Main entry point for standalone execution."""
    # Generate synthetic test data
    np.random.seed(42)
    n_observations = 1000
    
    # Create normal scores with some anomalies
    normal_scores = np.random.normal(loc=0.0, scale=1.0, size=int(0.9 * n_observations))
    anomaly_scores = np.random.normal(loc=3.0, scale=0.5, size=int(0.1 * n_observations))
    scores = np.concatenate([normal_scores, anomaly_scores])
    
    # Calibrate threshold
    calibrator = ThresholdCalibrator()
    result = calibrator.calibrate(scores)
    
    # Print results
    print("=" * 60)
    print("THRESHOLD CALIBRATION RESULTS")
    print("=" * 60)
    print(f"Threshold: {result.threshold:.4f}")
    print(f"Anomaly Rate: {result.anomaly_rate:.4f} ({result.anomaly_rate*100:.2f}%)")
    print(f"Validation: {'PASSED' if result.validation_passed else 'FAILED'}")
    print(f"Num Observations: {result.num_observations}")
    print(f"Num Anomalies Detected: {result.num_anomalies_detected}")
    print(f"Score Percentiles:")
    for k, v in result.score_percentiles.items():
        print(f"  {k}: {v:.4f}")
    print("=" * 60)


if __name__ == '__main__':
    main()
