"""
Self-Calibrating Conformal Prediction Wrapper for Time-Series Forecasts.

This module implements a CPU-optimized conformal prediction wrapper that adjusts
predictive intervals to achieve nominal coverage levels. It uses a fixed-size
calibration set and avoids nested cross-validation for efficiency.

The implementation follows the Self-Calibrating Conformal Prediction method,
which adjusts interval widths based on empirical coverage of a calibration set.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List, Union

from utils.logger import get_logger
from utils.exceptions import CalibrationError, DataValidationError

logger = get_logger(__name__)

# Fixed sample size for calibration to ensure CPU optimization
# and avoid nested CV as per Spec requirements
DEFAULT_CALIBRATION_SAMPLE_SIZE = 500
DEFAULT_ALPHA = 0.1  # Default for 90% coverage
DEFAULT_MIN_ITERATIONS = 3
DEFAULT_MAX_ITERATIONS = 10
DEFAULT_TOLERANCE = 0.01

class SelfCalibratingConformalWrapper:
    """
    Self-Calibrating Conformal Prediction Wrapper.

    This wrapper takes base model forecasts and adjusts their predictive intervals
    to achieve the desired nominal coverage level using a calibration set.

    Attributes:
        alpha: Target miscoverage level (1 - desired coverage).
        calibration_sample_size: Fixed number of samples for calibration.
        min_iterations: Minimum number of calibration iterations.
        max_iterations: Maximum number of calibration iterations.
        tolerance: Convergence tolerance for coverage adjustment.
    """

    def __init__(
        self,
        alpha: float = DEFAULT_ALPHA,
        calibration_sample_size: int = DEFAULT_CALIBRATION_SAMPLE_SIZE,
        min_iterations: int = DEFAULT_MIN_ITERATIONS,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        tolerance: float = DEFAULT_TOLERANCE
    ):
        if not 0 < alpha < 1:
            raise DataValidationError(f"Alpha must be between 0 and 1, got {alpha}")
        if calibration_sample_size <= 0:
            raise DataValidationError(f"Calibration sample size must be positive, got {calibration_sample_size}")

        self.alpha = alpha
        self.target_coverage = 1.0 - alpha
        self.calibration_sample_size = calibration_sample_size
        self.min_iterations = min_iterations
        self.max_iterations = max_iterations
        self.tolerance = tolerance

        # State to store calibration results
        self.calibrated_factor: Optional[float] = None
        self.calibration_coverage: Optional[float] = None
        self.calibration_error: Optional[float] = None

    def _compute_nonconformity_scores(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        lower_bound: np.ndarray,
        upper_bound: np.ndarray
    ) -> np.ndarray:
        """
        Compute nonconformity scores as the maximum of normalized residuals.

        For each point i, the score is:
            s_i = max( (y_i - upper_i) / sigma_i, (lower_i - y_i) / sigma_i )
        where sigma_i is a scale factor (here, we use the interval width).

        Args:
            y_true: True values.
            y_pred: Point forecasts.
            lower_bound: Lower bounds of intervals.
            upper_bound: Upper bounds of intervals.

        Returns:
            Array of nonconformity scores.
        """
        # Compute interval widths to normalize residuals
        interval_widths = upper_bound - lower_bound

        # Avoid division by zero
        interval_widths = np.maximum(interval_widths, 1e-8)

        # Compute residuals
        residuals_upper = (y_true - upper_bound) / interval_widths
        residuals_lower = (lower_bound - y_true) / interval_widths

        # Nonconformity score is the max of the two (absolute deviation from interval)
        scores = np.maximum(residuals_upper, residuals_lower)

        return scores

    def _compute_adjusted_coverage(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        lower_bound: np.ndarray,
        upper_bound: np.ndarray,
        adjustment_factor: float
    ) -> Tuple[float, np.ndarray, np.ndarray]:
        """
        Compute coverage with adjusted intervals.

        Args:
            y_true: True values.
            y_pred: Point forecasts.
            lower_bound: Original lower bounds.
            upper_bound: Original upper bounds.
            adjustment_factor: Factor to scale interval widths.

        Returns:
            Tuple of (empirical coverage, adjusted lower bounds, adjusted upper bounds).
        """
        # Adjust intervals by scaling the width
        widths = upper_bound - lower_bound
        adjusted_widths = widths * adjustment_factor

        adjusted_lower = y_pred - (y_pred - lower_bound) * adjustment_factor
        adjusted_upper = y_pred + (upper_bound - y_pred) * adjustment_factor

        # Compute coverage
        covered = (y_true >= adjusted_lower) & (y_true <= adjusted_upper)
        coverage = np.mean(covered)

        return coverage, adjusted_lower, adjusted_upper

    def calibrate(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        lower_bound: np.ndarray,
        upper_bound: np.ndarray
    ) -> Dict[str, Any]:
        """
        Calibrate the conformal wrapper on a calibration set.

        This method computes the adjustment factor needed to achieve the
        target coverage level on the calibration set.

        Args:
            y_true: True values for calibration.
            y_pred: Point forecasts for calibration.
            lower_bound: Lower bounds of original intervals.
            upper_bound: Upper bounds of original intervals.

        Returns:
            Dictionary containing calibration results.
        """
        logger.info(f"Starting conformal calibration with {len(y_true)} samples")

        if len(y_true) != len(y_pred) or len(y_true) != len(lower_bound) or len(y_true) != len(upper_bound):
            raise DataValidationError(
                "Input arrays must have the same length"
            )

        # Use a fixed sample size for calibration (or all if smaller)
        n_samples = min(len(y_true), self.calibration_sample_size)
        indices = np.random.choice(len(y_true), size=n_samples, replace=False)

        y_cal = y_true[indices]
        pred_cal = y_pred[indices]
        lower_cal = lower_bound[indices]
        upper_cal = upper_bound[indices]

        # Binary search for the adjustment factor
        factor_low = 0.1
        factor_high = 5.0
        best_factor = 1.0

        logger.info(f"Calibrating over {self.max_iterations} iterations")

        for iteration in range(self.max_iterations):
            # Try middle factor
            factor_mid = (factor_low + factor_high) / 2.0

            coverage, _, _ = self._compute_adjusted_coverage(
                y_cal, pred_cal, lower_cal, upper_cal, factor_mid
            )

            logger.debug(f"Iteration {iteration}: factor={factor_mid:.4f}, coverage={coverage:.4f}")

            if coverage < self.target_coverage:
                # Need wider intervals
                factor_low = factor_mid
            else:
                # Coverage is sufficient, try narrower
                best_factor = factor_mid
                factor_high = factor_mid

            # Check convergence
            if iteration >= self.min_iterations:
                if abs(coverage - self.target_coverage) < self.tolerance:
                    logger.info(f"Convergence reached at iteration {iteration}")
                    break

            # Safety check to avoid infinite loops
            if factor_high - factor_low < 1e-6:
                logger.warning("Factor range too small, stopping early")
                break

        # Final calibration
        self.calibrated_factor = best_factor
        coverage, _, _ = self._compute_adjusted_coverage(
            y_cal, pred_cal, lower_cal, upper_cal, best_factor
        )
        self.calibration_coverage = coverage

        # Compute mean absolute error on calibration set
        self.calibration_error = np.mean(np.abs(y_cal - pred_cal))

        logger.info(f"Calibration complete: factor={best_factor:.4f}, coverage={coverage:.4f}")

        return {
            "calibrated_factor": best_factor,
            "calibration_coverage": coverage,
            "target_coverage": self.target_coverage,
            "calibration_samples": n_samples,
            "calibration_error": self.calibration_error,
            "iterations": iteration + 1
        }

    def apply(
        self,
        y_pred: np.ndarray,
        lower_bound: np.ndarray,
        upper_bound: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Apply conformal adjustment to new forecasts.

        Args:
            y_pred: Point forecasts.
            lower_bound: Lower bounds of original intervals.
            upper_bound: Upper bounds of original intervals.

        Returns:
            Tuple of (adjusted lower bounds, adjusted upper bounds, adjustment factor).
        """
        if self.calibrated_factor is None:
            raise CalibrationError(
                "Wrapper not calibrated. Call calibrate() before apply()."
            )

        factor = self.calibrated_factor

        # Adjust intervals
        widths = upper_bound - lower_bound
        adjusted_widths = widths * factor

        adjusted_lower = y_pred - (y_pred - lower_bound) * factor
        adjusted_upper = y_pred + (upper_bound - y_pred) * factor

        return adjusted_lower, adjusted_upper, factor

    def get_coverage_stats(
        self,
        y_true: np.ndarray,
        lower_bound: np.ndarray,
        upper_bound: np.ndarray
    ) -> Dict[str, float]:
        """
        Compute coverage statistics for a given set of intervals.

        Args:
            y_true: True values.
            lower_bound: Lower bounds of intervals.
            upper_bound: Upper bounds of intervals.

        Returns:
            Dictionary with coverage statistics.
        """
        covered = (y_true >= lower_bound) & (y_true <= upper_bound)
        coverage = np.mean(covered)
        deviation = coverage - self.target_coverage

        return {
            "empirical_coverage": float(coverage),
            "target_coverage": float(self.target_coverage),
            "coverage_deviation": float(deviation),
            "n_samples": int(len(y_true))
        }


def compare_baseline_vs_conformal(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    lower_bound: np.ndarray,
    upper_bound: np.ndarray,
    alpha: float = DEFAULT_ALPHA,
    calibration_size: int = DEFAULT_CALIBRATION_SAMPLE_SIZE
) -> Dict[str, Any]:
    """
    Compare baseline coverage vs. conformal adjusted coverage.

    This is a convenience function that creates a wrapper, calibrates it,
    applies it, and compares the results.

    Args:
        y_true: True values.
        y_pred: Point forecasts.
        lower_bound: Lower bounds of original intervals.
        upper_bound: Upper bounds of original intervals.
        alpha: Target miscoverage level.
        calibration_size: Size of calibration set.

    Returns:
        Dictionary containing comparison results.
    """
    wrapper = SelfCalibratingConformalWrapper(
        alpha=alpha,
        calibration_sample_size=calibration_size
    )

    # Calibrate
    cal_results = wrapper.calibrate(y_true, y_pred, lower_bound, upper_bound)

    # Apply to full set (or a subset if desired)
    adj_lower, adj_upper, factor = wrapper.apply(y_pred, lower_bound, upper_bound)

    # Compute baseline coverage
    baseline_coverage = np.mean((y_true >= lower_bound) & (y_true <= upper_bound))

    # Compute conformal coverage
    conformal_coverage = np.mean((y_true >= adj_lower) & (y_true <= adj_upper))

    # Compute coverage deviations
    target_coverage = 1.0 - alpha
    baseline_deviation = baseline_coverage - target_coverage
    conformal_deviation = conformal_coverage - target_coverage

    return {
        "baseline": {
            "coverage": float(baseline_coverage),
            "deviation": float(baseline_deviation)
        },
        "conformal": {
            "coverage": float(conformal_coverage),
            "deviation": float(conformal_deviation),
            "adjustment_factor": float(factor)
        },
        "target_coverage": float(target_coverage),
        "calibration_results": cal_results
    }


def aggregate_conformal_results(
    results_list: List[Dict[str, Any]]
) -> pd.DataFrame:
    """
    Aggregate conformal comparison results from multiple series/models.

    Args:
        results_list: List of result dictionaries from compare_baseline_vs_conformal.

    Returns:
        DataFrame with aggregated results.
    """
    rows = []
    for i, result in enumerate(results_list):
        row = {
            "series_id": result.get("series_id", f"series_{i}"),
            "model_name": result.get("model_name", "unknown"),
            "baseline_coverage": result["baseline"]["coverage"],
            "baseline_deviation": result["baseline"]["deviation"],
            "conformal_coverage": result["conformal"]["coverage"],
            "conformal_deviation": result["conformal"]["deviation"],
            "adjustment_factor": result["conformal"]["adjustment_factor"],
            "target_coverage": result["target_coverage"],
            "calibration_samples": result["calibration_results"]["calibration_samples"],
            "calibration_factor": result["calibration_results"]["calibrated_factor"],
            "calibration_coverage": result["calibration_results"]["calibration_coverage"]
        }
        rows.append(row)

    return pd.DataFrame(rows)


def conformal_results_to_dataframe(
    results: Dict[str, Any]
) -> pd.DataFrame:
    """
    Convert a single conformal comparison result to a DataFrame.

    Args:
        results: Result dictionary from compare_baseline_vs_conformal.

    Returns:
        DataFrame with the result.
    """
    row = {
        "baseline_coverage": results["baseline"]["coverage"],
        "baseline_deviation": results["baseline"]["deviation"],
        "conformal_coverage": results["conformal"]["coverage"],
        "conformal_deviation": results["conformal"]["deviation"],
        "adjustment_factor": results["conformal"]["adjustment_factor"],
        "target_coverage": results["target_coverage"]
    }
    return pd.DataFrame([row])
