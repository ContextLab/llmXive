import logging
import numpy as np
from typing import Tuple, Union, Optional

from utils.logger import get_logger

logger = get_logger(__name__)


def calculate_calibration_error(
    predictions: Union[np.ndarray, list],
    intervals: Union[np.ndarray, list],
    ground_truth: Union[np.ndarray, list],
    nominal_level: float = 0.9
) -> float:
    """
    Calculate the absolute calibration error (|Observed Coverage - Nominal Coverage|).

    Args:
        predictions: Array of point predictions (not used directly for coverage but kept for signature).
        intervals: Array of shape (N, 2) where each row is [lower_bound, upper_bound].
        ground_truth: Array of true values.
        nominal_level: The target coverage probability (e.g., 0.9 for 90%).

    Returns:
        float: The absolute difference between observed and nominal coverage.
    """
    if len(predictions) != len(ground_truth):
        raise ValueError("Length of predictions must match length of ground_truth.")
    if intervals.shape[0] != len(ground_truth):
        raise ValueError("Number of intervals must match length of ground_truth.")
    if intervals.shape[1] != 2:
        raise ValueError("Intervals must be of shape (N, 2).")

    lower_bounds = intervals[:, 0]
    upper_bounds = intervals[:, 1]

    # Check if ground truth falls within the interval
    contained = (ground_truth >= lower_bounds) & (ground_truth <= upper_bounds)
    observed_coverage = np.mean(contained)

    calibration_error = abs(observed_coverage - nominal_level)
    logger.debug(f"Calibration Error: {calibration_error:.4f} (Observed: {observed_coverage:.4f}, Nominal: {nominal_level})")

    return float(calibration_error)


def calculate_sharpness(intervals: Union[np.ndarray, list]) -> float:
    """
    Calculate the Prediction Interval Sharpness.

    Sharpness is defined as the mean width of the prediction intervals.
    Lower sharpness values indicate tighter (sharper) intervals, which is desirable
    provided calibration is maintained.

    Args:
        intervals: Array of shape (N, 2) where each row is [lower_bound, upper_bound].

    Returns:
        float: The mean interval width.
    """
    if isinstance(intervals, list):
        intervals = np.array(intervals)

    if intervals.shape[0] == 0:
        logger.warning("Empty intervals provided for sharpness calculation. Returning 0.0.")
        return 0.0

    if intervals.shape[1] != 2:
        raise ValueError("Intervals must be of shape (N, 2).")

    lower_bounds = intervals[:, 0]
    upper_bounds = intervals[:, 1]

    # Calculate width for each sample
    widths = upper_bounds - lower_bounds

    # Sharpness is the average width
    sharpness = float(np.mean(widths))

    logger.debug(f"Sharpness: {sharpness:.4f} (Mean Width)")
    return sharpness


def calculate_interval_coverage(
    intervals: Union[np.ndarray, list],
    ground_truth: Union[np.ndarray, list]
) -> float:
    """
    Calculate the observed coverage rate (fraction of ground truth values inside intervals).

    Args:
        intervals: Array of shape (N, 2) where each row is [lower_bound, upper_bound].
        ground_truth: Array of true values.

    Returns:
        float: The observed coverage probability (0.0 to 1.0).
    """
    if isinstance(intervals, list):
        intervals = np.array(intervals)
    if isinstance(ground_truth, list):
        ground_truth = np.array(ground_truth)

    if intervals.shape[0] != len(ground_truth):
        raise ValueError("Number of intervals must match length of ground_truth.")
    if intervals.shape[1] != 2:
        raise ValueError("Intervals must be of shape (N, 2).")

    lower_bounds = intervals[:, 0]
    upper_bounds = intervals[:, 1]

    contained = (ground_truth >= lower_bounds) & (ground_truth <= upper_bounds)
    coverage = float(np.mean(contained))

    logger.debug(f"Observed Coverage: {coverage:.4f}")
    return coverage


def calculate_mean_interval_width(intervals: Union[np.ndarray, list]) -> float:
    """
    Alias for calculate_sharpness. Returns the mean width of prediction intervals.

    Args:
        intervals: Array of shape (N, 2) where each row is [lower_bound, upper_bound].

    Returns:
        float: The mean interval width.
    """
    return calculate_sharpness(intervals)