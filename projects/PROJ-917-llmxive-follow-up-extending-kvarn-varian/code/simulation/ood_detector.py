"""
Out-of-Distribution (OOD) Detection mechanism for KVarN simulation.

This module implements the edge case handling logic required by the spec:
1. Epsilon floor checks (numerical stability).
2. Outlier magnitude thresholding.
3. Statistical distance metric (Mahalanobis-like or Z-score) based on training set moments.
"""

import numpy as np
import logging
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

# Import config to access thresholds if defined, otherwise use defaults
try:
    from config import get_config
    CONFIG = get_config()
    # Defaults if not in config or to override
    DEFAULT_EPSILON_FLOOR = getattr(CONFIG, 'EPSILON_FLOOR', 1e-6)
    DEFAULT_OUTLIER_THRESHOLD = getattr(CONFIG, 'OUTLIER_THRESHOLD', 10.0)
    DEFAULT_MOMENT_STD_FACTOR = getattr(CONFIG, 'MOMENT_STD_FACTOR', 3.0)
except (ImportError, AttributeError):
    DEFAULT_EPSILON_FLOOR = 1e-6
    DEFAULT_OUTLIER_THRESHOLD = 10.0
    DEFAULT_MOMENT_STD_FACTOR = 3.0

logger = logging.getLogger(__name__)


@dataclass
class OODResult:
    """Result of OOD detection."""
    is_ood: bool
    reason: str
    confidence_score: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


class OODDetector:
    """
    Detects Out-of-Distribution samples based on statistical moments.

    Requirements:
    - Explicitly implements epsilon floor check.
    - Explicitly implements outlier threshold logic.
    - Computes statistical distance using training set std.
    - Returns boolean flag and optional confidence score.
    """

    def __init__(
        self,
        training_moments_path: Optional[Path] = None,
        epsilon_floor: float = DEFAULT_EPSILON_FLOOR,
        outlier_threshold: float = DEFAULT_OUTLIER_THRESHOLD,
        std_factor: float = DEFAULT_MOMENT_STD_FACTOR
    ):
        """
        Initialize the detector.

        Args:
            training_moments_path: Path to a CSV containing training set statistics
                                   (columns: 'mean', 'variance', 'sparsity', 'outlier_magnitude').
                                   If None, assumes no reference distribution for statistical check.
            epsilon_floor: Minimum allowed value for variance/mean to avoid division by zero.
            outlier_threshold: Maximum allowed magnitude for outlier_magnitude field.
            std_factor: Number of standard deviations for the statistical threshold.
        """
        self.epsilon_floor = epsilon_floor
        self.outlier_threshold = outlier_threshold
        self.std_factor = std_factor
        self.training_stats: Optional[Dict[str, np.ndarray]] = None

        if training_moments_path and training_moments_path.exists():
            self._load_training_stats(training_moments_path)
        elif training_moments_path:
            logger.warning(f"Training moments path provided but file not found: {training_moments_path}. "
                           "Statistical OOD check will be skipped.")

    def _load_training_stats(self, path: Path) -> None:
        """Load mean and std of training moments from a CSV."""
        import pandas as pd
        try:
            df = pd.read_csv(path)
            # We need the mean and std of the training distribution for Z-score calculation
            self.training_stats = {
                'mean': df[['mean', 'variance', 'sparsity', 'outlier_magnitude']].mean().to_dict(),
                'std': df[['mean', 'variance', 'sparsity', 'outlier_magnitude']].std().to_dict()
            }
            logger.info(f"Loaded training statistics from {path}")
        except Exception as e:
            logger.error(f"Failed to load training statistics from {path}: {e}")
            self.training_stats = None

    def check_numerical_stability(self, moments: Dict[str, float]) -> Tuple[bool, str]:
        """
        Check for epsilon floor violations and numerical instability.

        Args:
            moments: Dictionary containing 'mean', 'variance', 'sparsity', 'outlier_magnitude'.

        Returns:
            Tuple of (is_stable, reason_string).
        """
        # 1. Check for NaN or Inf
        for key, val in moments.items():
            if not np.isfinite(val):
                return False, f"Non-finite value detected in {key}: {val}"

        # 2. Epsilon floor check (Spec Edge Cases)
        # Variance must be >= epsilon_floor to avoid division by zero in quantization/noise models
        if moments.get('variance', 0.0) < self.epsilon_floor:
            return False, f"Variance {moments['variance']} < epsilon_floor {self.epsilon_floor}"

        # Mean can be negative, but magnitude check might be relevant if spec implies positive-only
        # For now, strict epsilon floor on variance is the primary stability check.
        return True, "Numerical stability check passed"

    def check_outlier_threshold(self, moments: Dict[str, float]) -> Tuple[bool, str]:
        """
        Check if outlier magnitude exceeds the defined threshold.

        Args:
            moments: Dictionary containing 'outlier_magnitude'.

        Returns:
            Tuple of (is_valid, reason_string).
        """
        outlier_mag = moments.get('outlier_magnitude', 0.0)
        if outlier_mag > self.outlier_threshold:
            return False, f"Outlier magnitude {outlier_mag} exceeds threshold {self.outlier_threshold}"
        return True, "Outlier threshold check passed"

    def check_statistical_distance(self, moments: Dict[str, float]) -> Tuple[bool, str, Optional[float]]:
        """
        Compute statistical distance using training set std (Z-score).

        Returns:
            Tuple of (is_ood, reason, z_score).
            If no training stats are loaded, returns (False, "No reference data", None).
        """
        if not self.training_stats:
            return False, "No reference training distribution loaded", None

        max_z_score = 0.0
        reasons = []

        for key in ['mean', 'variance', 'sparsity', 'outlier_magnitude']:
            if key not in moments:
                continue

            val = moments[key]
            mu = self.training_stats['mean'][key]
            sigma = self.training_stats['std'][key]

            # Avoid division by zero if std is 0 (constant feature in training)
            if sigma < 1e-9:
                if abs(val - mu) > 1e-6:
                    reasons.append(f"{key} deviates from constant training value")
                    max_z_score = max(max_z_score, 100.0) # Effectively infinite
                continue

            z = abs(val - mu) / sigma
            max_z_score = max(max_z_score, z)

            if z > self.std_factor:
                reasons.append(f"{key} z-score ({z:.2f}) > {self.std_factor}")

        is_ood = len(reasons) > 0
        reason_str = "; ".join(reasons) if reasons else "Within statistical bounds"
        return is_ood, reason_str, max_z_score

    def detect(self, moments: Dict[str, float]) -> OODResult:
        """
        Main entry point for OOD detection.

        Performs checks in order:
        1. Numerical Stability (Epsilon floor)
        2. Outlier Threshold
        3. Statistical Distance (if reference available)

        Args:
            moments: Dictionary with keys: mean, variance, sparsity, outlier_magnitude.

        Returns:
            OODResult object.
        """
        # 1. Numerical Stability
        is_stable, stability_reason = self.check_numerical_stability(moments)
        if not is_stable:
            return OODResult(
                is_ood=True,
                reason=f"Numerical instability: {stability_reason}",
                confidence_score=1.0,
                details={'check': 'numerical_stability', 'value': moments.get('variance')}
            )

        # 2. Outlier Threshold
        is_valid_outlier, outlier_reason = self.check_outlier_threshold(moments)
        if not is_valid_outlier:
            return OODResult(
                is_ood=True,
                reason=f"Outlier threshold exceeded: {outlier_reason}",
                confidence_score=1.0,
                details={'check': 'outlier_threshold', 'value': moments.get('outlier_magnitude')}
            )

        # 3. Statistical Distance
        is_stat_ood, stat_reason, z_score = self.check_statistical_distance(moments)
        if is_stat_ood:
            return OODResult(
                is_ood=True,
                reason=f"Statistical OOD: {stat_reason}",
                confidence_score=float(min(z_score / self.std_factor, 1.0)) if z_score else 0.0,
                details={'check': 'statistical_distance', 'max_z_score': z_score}
            )

        return OODResult(
            is_ood=False,
            reason="All checks passed",
            confidence_score=1.0,
            details={'check': 'all', 'z_score': z_score}
        )


def detect_ood(
    moments: Dict[str, float],
    training_moments_path: Optional[Path] = None,
    epsilon_floor: Optional[float] = None,
    outlier_threshold: Optional[float] = None
) -> OODResult:
    """
    Convenience function to run OOD detection without instantiating the class.

    Args:
        moments: Input moments dictionary.
        training_moments_path: Path to training stats CSV.
        epsilon_floor: Override default epsilon floor.
        outlier_threshold: Override default outlier threshold.

    Returns:
        OODResult.
    """
    detector = OODDetector(
        training_moments_path=training_moments_path,
        epsilon_floor=epsilon_floor or DEFAULT_EPSILON_FLOOR,
        outlier_threshold=outlier_threshold or DEFAULT_OUTLIER_THRESHOLD
    )
    return detector.detect(moments)
