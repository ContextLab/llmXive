"""
Threshold Calibration Module for Anomaly Detection

Implements adaptive threshold computation and calibration for anomaly detection
across single and multiple datasets without labeled data.

US3 Acceptance Scenario 3: Support for threshold calibration across multiple
datasets without labeled data.

API Surface:
  - ThresholdCalibrator: Class for threshold calibration
  - calibrate_threshold(): Single dataset calibration
  - calibrate_threshold_multi_dataset(): Multi-dataset calibration
  - validate_threshold(): Validate threshold produces reasonable anomaly rates
  - compute_expected_bounds(): Compute expected anomaly rate bounds
  - get_decision_boundary(): Retrieve current decision boundary
  - update_decision_boundary(): Update decision boundary
  - compute_multi_dataset_threshold(): Unified threshold across datasets
  - save_threshold_config(): Save calibrated threshold to config
  - load_threshold_config(): Load threshold from config
  - main(): CLI entry point
"""

import os
import sys
import json
import logging
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass, field, asdict

import numpy as np
from scipy import stats

# Import from project modules
try:
    from src.models.anomaly_score import AnomalyScore
except ImportError:
    from code.src.models.anomaly_score import AnomalyScore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ThresholdConfig:
    """Configuration for threshold calibration."""
    percentile: float = 0.95  # Default 95th percentile
    min_anomaly_rate: float = 0.01  # Minimum expected anomaly rate
    max_anomaly_rate: float = 0.10  # Maximum expected anomaly rate
    target_anomaly_rate: float = 0.05  # Target anomaly rate
    alpha: float = 0.05  # Significance level for statistical tests
    multi_dataset_weighting: str = 'uniform'  # 'uniform', 'sample_size', 'variance'
    min_samples_per_dataset: int = 100  # Minimum samples required per dataset
    enable_robust_calibration: bool = True  # Use robust statistics
    outlier_removal: bool = True  # Remove extreme outliers before calibration
    outlier_std_threshold: float = 5.0  # Standard deviations for outlier removal
    confidence_interval: float = 0.95  # Confidence level for bounds
    version: str = '1.0'
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ThresholdResult:
    """Result of threshold calibration."""
    threshold: float
    anomaly_rate: float
    expected_bounds: Tuple[float, float]
    calibration_method: str
    dataset_id: Optional[str] = None
    num_samples: int = 0
    score_statistics: Dict[str, float] = field(default_factory=dict)
    confidence_interval: Tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))
    calibrated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    validation_passed: bool = True
    validation_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiDatasetThresholdResult:
    """Result of multi-dataset threshold calibration."""
    unified_threshold: float
    per_dataset_results: Dict[str, ThresholdResult] = field(default_factory=dict)
    anomaly_rates: Dict[str, float] = field(default_factory=dict)
    expected_bounds: Tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))
    calibration_method: str = "multi_dataset_adaptive"
    num_datasets: int = 0
    total_samples: int = 0
    validation_passed: bool = True
    validation_message: str = ""
    statistics: Dict[str, Any] = field(default_factory=dict)
    calibrated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ThresholdCalibrator:
    """
    Threshold Calibrator for Anomaly Detection.

    Supports both single dataset and multi-dataset threshold calibration
    for unlabeled time series data.

    US3 Acceptance Scenarios:
      - Scenario 1: Anomaly rate validation against expected bounds
      - Scenario 2: Decision boundary documentation in config.yaml
      - Scenario 3: Multi-dataset threshold calibration without labels
    """

    def __init__(self, config: Optional[ThresholdConfig] = None):
        """
        Initialize the threshold calibrator.

        Args:
            config: ThresholdConfig instance or None for defaults
        """
        self.config = config or ThresholdConfig()
        self._current_threshold: Optional[float] = None
        self._current_result: Optional[ThresholdResult] = None
        self._calibration_history: List[Dict[str, Any]] = []

    def calibrate_threshold(
        self,
        scores: Union[np.ndarray, List[float]],
        dataset_id: Optional[str] = None
    ) -> ThresholdResult:
        """
        Calibrate threshold for a single dataset.

        Args:
            scores: Array of anomaly scores
            dataset_id: Optional identifier for the dataset

        Returns:
            ThresholdResult with calibrated threshold and validation
        """
        scores = np.asarray(scores, dtype=np.float64)
        num_samples = len(scores)

        if num_samples < self.config.min_samples_per_dataset:
            raise ValueError(
                f"Insufficient samples: {num_samples} < "
                f"{self.config.min_samples_per_dataset}"
            )

        # Remove extreme outliers if enabled
        if self.config.outlier_removal:
            scores_clean = self._remove_extreme_outliers(scores)
            logger.info(
                f"Removed {num_samples - len(scores_clean)} extreme outliers"
            )
        else:
            scores_clean = scores

        # Compute threshold based on percentile
        threshold = np.percentile(scores_clean, self.config.percentile * 100)

        # Compute score statistics
        score_stats = self._compute_score_statistics(scores_clean)

        # Compute expected anomaly rate bounds
        expected_bounds = self._compute_expected_bounds(num_samples)

        # Validate threshold produces reasonable anomaly rate
        validation_passed, validation_message = self._validate_threshold(
            scores_clean, threshold, expected_bounds
        )

        # Compute confidence interval for anomaly rate
        anomaly_rate = np.mean(scores_clean > threshold)
        ci = self._compute_anomaly_rate_confidence_interval(
            anomaly_rate, num_samples
        )

        result = ThresholdResult(
            threshold=threshold,
            anomaly_rate=anomaly_rate,
            expected_bounds=expected_bounds,
            calibration_method="percentile_adaptive",
            dataset_id=dataset_id,
            num_samples=num_samples,
            score_statistics=score_stats,
            confidence_interval=ci,
            validation_passed=validation_passed,
            validation_message=validation_message
        )

        self._current_threshold = threshold
        self._current_result = result
        self._calibration_history.append(asdict(result))

        logger.info(
            f"Threshold calibrated: {threshold:.6f}, "
            f"anomaly_rate: {anomaly_rate:.4f}"
        )

        return result

    def calibrate_threshold_multi_dataset(
        self,
        dataset_scores: Dict[str, Union[np.ndarray, List[float]]],
        weighting: Optional[str] = None
    ) -> MultiDatasetThresholdResult:
        """
        Calibrate unified threshold across multiple datasets.

        This is the implementation for US3 Acceptance Scenario 3.

        Args:
            dataset_scores: Dict mapping dataset_id to anomaly scores
            weighting: Weighting method for combining thresholds
                      'uniform', 'sample_size', 'variance'

        Returns:
            MultiDatasetThresholdResult with unified threshold and per-dataset
            validation
        """
        if len(dataset_scores) == 0:
            raise ValueError("No datasets provided for calibration")

        weighting = weighting or self.config.multi_dataset_weighting

        logger.info(
            f"Multi-dataset calibration: {len(dataset_scores)} datasets, "
            f"weighting={weighting}"
        )

        # Validate minimum samples per dataset
        for dataset_id, scores in dataset_scores.items():
            num_samples = len(np.asarray(scores))
            if num_samples < self.config.min_samples_per_dataset:
                raise ValueError(
                    f"Dataset '{dataset_id}' has insufficient samples: "
                    f"{num_samples} < {self.config.min_samples_per_dataset}"
                )

        # Calibrate threshold for each dataset individually
        per_dataset_results = {}
        thresholds = []
        sample_sizes = []
        variance_weights = []

        for dataset_id, scores in dataset_scores.items():
            result = self.calibrate_threshold(scores, dataset_id)
            per_dataset_results[dataset_id] = result
            thresholds.append(result.threshold)
            sample_sizes.append(result.num_samples)

            # Compute variance weight if needed
            if result.score_statistics.get('variance', 0) > 0:
                variance_weights.append(1.0 / result.score_statistics['variance'])
            else:
                variance_weights.append(1.0)

        # Compute unified threshold based on weighting method
        if weighting == 'uniform':
            unified_threshold = np.mean(thresholds)
        elif weighting == 'sample_size':
            # Weight by sample size
            weights = np.array(sample_sizes) / sum(sample_sizes)
            unified_threshold = np.average(thresholds, weights=weights)
        elif weighting == 'variance':
            # Weight by inverse variance (more stable datasets get higher weight)
            weights = np.array(variance_weights) / sum(variance_weights)
            unified_threshold = np.average(thresholds, weights=weights)
        else:
            logger.warning(f"Unknown weighting '{weighting}', using uniform")
            unified_threshold = np.mean(thresholds)

        # Validate unified threshold across all datasets
        validation_passed = True
        validation_messages = []
        anomaly_rates = {}

        for dataset_id, scores in dataset_scores.items():
            scores_arr = np.asarray(scores)
            rate = np.mean(scores_arr > unified_threshold)
            anomaly_rates[dataset_id] = rate

            # Check if rate is within bounds
            bounds = self._compute_expected_bounds(len(scores_arr))
            if not (bounds[0] <= rate <= bounds[1]):
                validation_passed = False
                validation_messages.append(
                    f"Dataset '{dataset_id}': rate {rate:.4f} outside "
                    f"bounds [{bounds[0]:.4f}, {bounds[1]:.4f}]"
                )

        # Compute overall statistics
        all_scores = np.concatenate([
            np.asarray(scores) for scores in dataset_scores.values()
        ])
        expected_bounds = self._compute_expected_bounds(len(all_scores))

        result = MultiDatasetThresholdResult(
            unified_threshold=unified_threshold,
            per_dataset_results=per_dataset_results,
            anomaly_rates=anomaly_rates,
            expected_bounds=expected_bounds,
            calibration_method="multi_dataset_adaptive",
            num_datasets=len(dataset_scores),
            total_samples=len(all_scores),
            validation_passed=validation_passed,
            validation_message="; ".join(validation_messages) if validation_messages else "All datasets within bounds",
            statistics={
                'individual_thresholds': thresholds,
                'weighting_method': weighting,
                'threshold_variance': np.var(thresholds),
                'threshold_range': (min(thresholds), max(thresholds))
            }
        )

        logger.info(
            f"Unified threshold: {unified_threshold:.6f}, "
            f"datasets: {len(dataset_scores)}, "
            f"validation: {'PASSED' if validation_passed else 'FAILED'}"
        )

        return result

    def validate_threshold(
        self,
        scores: Union[np.ndarray, List[float]],
        threshold: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Validate that a threshold produces reasonable anomaly rates.

        Args:
            scores: Array of anomaly scores
            threshold: Threshold to validate (uses current if None)

        Returns:
            Tuple of (validation_passed, message)
        """
        threshold = threshold if threshold is not None else self._current_threshold

        if threshold is None:
            return False, "No threshold set for validation"

        scores = np.asarray(scores, dtype=np.float64)
        anomaly_rate = np.mean(scores > threshold)
        expected_bounds = self._compute_expected_bounds(len(scores))

        if expected_bounds[0] <= anomaly_rate <= expected_bounds[1]:
            return True, (
                f"Anomaly rate {anomaly_rate:.4f} within expected bounds "
                f"[{expected_bounds[0]:.4f}, {expected_bounds[1]:.4f}]"
            )
        else:
            return False, (
                f"Anomaly rate {anomaly_rate:.4f} outside expected bounds "
                f"[{expected_bounds[0]:.4f}, {expected_bounds[1]:.4f}]"
            )

    def compute_expected_bounds(self, num_samples: int) -> Tuple[float, float]:
        """
        Compute expected anomaly rate bounds based on sample size.

        Args:
            num_samples: Number of samples in the dataset

        Returns:
            Tuple of (min_rate, max_rate)
        """
        # Use the configured bounds
        return (
            self.config.min_anomaly_rate,
            self.config.max_anomaly_rate
        )

    def get_decision_boundary(self) -> Optional[float]:
        """
        Get the current decision boundary (threshold).

        Returns:
            Current threshold or None if not calibrated
        """
        return self._current_threshold

    def update_decision_boundary(self, threshold: float) -> None:
        """
        Update the decision boundary manually.

        Args:
            threshold: New threshold value
        """
        self._current_threshold = threshold
        logger.info(f"Decision boundary updated to: {threshold:.6f}")

    def _remove_extreme_outliers(self, scores: np.ndarray) -> np.ndarray:
        """
        Remove extreme outliers from scores using standard deviation threshold.

        Args:
            scores: Array of scores

        Returns:
            Array with extreme outliers removed
        """
        mean = np.mean(scores)
        std = np.std(scores)

        if std == 0:
            return scores

        mask = np.abs(scores - mean) <= self.config.outlier_std_threshold * std
        return scores[mask]

    def _compute_score_statistics(self, scores: np.ndarray) -> Dict[str, float]:
        """
        Compute statistics for a score array.

        Args:
            scores: Array of scores

        Returns:
            Dictionary of statistics
        """
        return {
            'mean': float(np.mean(scores)),
            'std': float(np.std(scores)),
            'min': float(np.min(scores)),
            'max': float(np.max(scores)),
            'median': float(np.median(scores)),
            'variance': float(np.var(scores)),
            'skewness': float(stats.skew(scores)),
            'kurtosis': float(stats.kurtosis(scores))
        }

    def _compute_anomaly_rate_confidence_interval(
        self,
        anomaly_rate: float,
        num_samples: int
    ) -> Tuple[float, float]:
        """
        Compute confidence interval for anomaly rate.

        Args:
            anomaly_rate: Observed anomaly rate
            num_samples: Number of samples

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if num_samples < 30:
            # Use exact binomial for small samples
            lower = stats.beta.ppf(
                (1 - self.config.confidence_interval) / 2,
                max(1, int(num_samples * anomaly_rate)),
                max(1, int(num_samples * (1 - anomaly_rate)))
            )
            upper = stats.beta.ppf(
                (1 + self.config.confidence_interval) / 2,
                max(1, int(num_samples * anomaly_rate) + 1),
                max(1, int(num_samples * (1 - anomaly_rate)) + 1)
            )
        else:
            # Use normal approximation for large samples
            se = np.sqrt(anomaly_rate * (1 - anomaly_rate) / num_samples)
            z = stats.norm.ppf((1 + self.config.confidence_interval) / 2)
            lower = max(0, anomaly_rate - z * se)
            upper = min(1, anomaly_rate + z * se)

        return (float(lower), float(upper))

    def _validate_threshold(
        self,
        scores: np.ndarray,
        threshold: float,
        expected_bounds: Tuple[float, float]
    ) -> Tuple[bool, str]:
        """
        Validate threshold produces acceptable anomaly rate.

        Args:
            scores: Array of scores
            threshold: Threshold to validate
            expected_bounds: Expected (min, max) anomaly rate bounds

        Returns:
            Tuple of (validation_passed, message)
        """
        anomaly_rate = np.mean(scores > threshold)

        if expected_bounds[0] <= anomaly_rate <= expected_bounds[1]:
            return True, f"Rate {anomaly_rate:.4f} within bounds"
        else:
            return False, f"Rate {anomaly_rate:.4f} outside bounds [{expected_bounds[0]:.4f}, {expected_bounds[1]:.4f}]"


def compute_multi_dataset_threshold(
    dataset_scores: Dict[str, Union[np.ndarray, List[float]]],
    config: Optional[ThresholdConfig] = None
) -> MultiDatasetThresholdResult:
    """
    Convenience function for multi-dataset threshold calibration.

    Args:
        dataset_scores: Dict mapping dataset_id to anomaly scores
        config: Optional ThresholdConfig

    Returns:
        MultiDatasetThresholdResult
    """
    calibrator = ThresholdCalibrator(config)
    return calibrator.calibrate_threshold_multi_dataset(dataset_scores)


def save_threshold_config(
    result: Union[ThresholdResult, MultiDatasetThresholdResult],
    output_path: Union[str, Path]
) -> None:
    """
    Save threshold calibration result to JSON/YAML file.

    Args:
        result: Calibration result to save
        output_path: Path to output file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(result, MultiDatasetThresholdResult):
        data = asdict(result)
    else:
        data = asdict(result)

    # Save as YAML
    with open(output_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Threshold config saved to: {output_path}")


def load_threshold_config(
    input_path: Union[str, Path]
) -> Union[ThresholdResult, MultiDatasetThresholdResult]:
    """
    Load threshold calibration result from JSON/YAML file.

    Args:
        input_path: Path to input file

    Returns:
        ThresholdResult or MultiDatasetThresholdResult
    """
    input_path = Path(input_path)

    with open(input_path, 'r') as f:
        data = yaml.safe_load(f)

    # Determine type based on fields
    if 'unified_threshold' in data:
        return MultiDatasetThresholdResult(**data)
    else:
        return ThresholdResult(**data)


def main():
    """CLI entry point for threshold calibration."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Threshold calibration for anomaly detection'
    )
    parser.add_argument(
        '--scores', type=str, required=True,
        help='Path to JSON file with scores (single or multi-dataset)'
    )
    parser.add_argument(
        '--output', type=str, required=True,
        help='Path to save threshold config'
    )
    parser.add_argument(
        '--percentile', type=float, default=0.95,
        help='Percentile for threshold computation'
    )
    parser.add_argument(
        '--weighting', type=str, default='uniform',
        choices=['uniform', 'sample_size', 'variance'],
        help='Weighting method for multi-dataset calibration'
    )
    parser.add_argument(
        '--validate', action='store_true',
        help='Validate threshold against expected bounds'
    )

    args = parser.parse_args()

    # Load scores
    with open(args.scores, 'r') as f:
        scores_data = json.load(f)

    # Determine if single or multi-dataset
    if isinstance(scores_data, dict) and 'threshold' in scores_data:
        # Single dataset result format
        scores = scores_data.get('scores', [])
        result = ThresholdCalibrator(
            ThresholdConfig(percentile=args.percentile)
        ).calibrate_threshold(scores)
    elif isinstance(scores_data, dict):
        # Multi-dataset: keys are dataset_ids, values are score arrays
        result = compute_multi_dataset_threshold(
            scores_data,
            ThresholdConfig(
                percentile=args.percentile,
                multi_dataset_weighting=args.weighting
            )
        )
    else:
        # Single dataset: list of scores
        result = ThresholdCalibrator(
            ThresholdConfig(percentile=args.percentile)
        ).calibrate_threshold(scores_data)

    # Validate if requested
    if args.validate:
        if isinstance(result, MultiDatasetThresholdResult):
            for dataset_id, ds_result in result.per_dataset_results.items():
              passed, msg = ds_result.validation_passed, ds_result.validation_message
              status = "✓" if passed else "✗"
              print(f"{status} {dataset_id}: {msg}")
        else:
            passed, msg = result.validation_passed, result.validation_message
            status = "✓" if passed else "✗"
            print(f"{status} {msg}")

    # Save result
    save_threshold_config(result, args.output)
    print(f"Threshold config saved to: {args.output}")


if __name__ == '__main__':
    main()
