"""
Statistical utilities for the llmXive code complexity research pipeline.

Provides segmented regression (change-point detection), bootstrap confidence
intervals, and correlation analysis functions.
"""

import numpy as np
from typing import Tuple, List, Dict, Any, Optional
from scipy import stats
from scipy.optimize import minimize_scalar
import warnings

# Suppress convergence warnings for cleaner output during optimization
warnings.filterwarnings('ignore', category=RuntimeWarning, module='scipy.optimize')


def pearson_correlation(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Calculate Pearson correlation coefficient and p-value.

    Args:
        x: First variable array.
        y: Second variable array.

    Returns:
        Tuple of (correlation coefficient, p-value).
    """
    if len(x) != len(y) or len(x) == 0:
        raise ValueError("Input arrays must be of equal non-zero length.")

    # Handle constant arrays
    if np.std(x) == 0 or np.std(y) == 0:
        return 0.0, 1.0

    corr, p_value = stats.pearsonr(x, y)
    return float(corr), float(p_value)


def spearman_correlation(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Calculate Spearman rank correlation coefficient and p-value.

    Args:
        x: First variable array.
        y: Second variable array.

    Returns:
        Tuple of (correlation coefficient, p-value).
    """
    if len(x) != len(y) or len(x) == 0:
        raise ValueError("Input arrays must be of equal non-zero length.")

    corr, p_value = stats.spearmanr(x, y)
    return float(corr), float(p_value)


def segmented_regression(x: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    Perform segmented regression (change-point detection) to identify a single
    breakpoint where the slope of the relationship between x and y changes.

    This uses a grid search approach to find the optimal change-point that
    minimizes the residual sum of squares (RSS) for a piecewise linear model.

    Args:
        x: Independent variable array.
        y: Dependent variable array.

    Returns:
        Dictionary containing:
            - 'change_point': The x-value of the detected change point.
            - 'slope1': Slope of the segment before the change point.
            - 'slope2': Slope of the segment after the change point.
            - 'intercept1': Intercept of the first segment.
            - 'intercept2': Intercept of the second segment.
            - 'rss': Residual sum of squares for the segmented model.
            - 'r_squared': R-squared value for the segmented model.
    """
    if len(x) != len(y) or len(x) < 10:
        raise ValueError("Need sufficient data points (>=10) for segmented regression.")

    # Sort data by x to ensure monotonicity for segmentation
    sort_idx = np.argsort(x)
    x_sorted = x[sort_idx]
    y_sorted = y[sort_idx]

    # Define a grid of potential change points (avoiding extremes)
    min_points = 5
    if len(x_sorted) <= 2 * min_points:
        # Fallback if data is too sparse
        change_point_candidates = [np.median(x_sorted)]
    else:
        # Use 20% to 80% of the range as candidates
        start_idx = int(len(x_sorted) * 0.2)
        end_idx = int(len(x_sorted) * 0.8)
        change_point_candidates = x_sorted[start_idx:end_idx]

    best_rss = np.inf
    best_params = None

    for cp in change_point_candidates:
        # Split data
        mask_left = x_sorted <= cp
        mask_right = x_sorted > cp

        # Ensure both segments have data
        if not np.any(mask_left) or not np.any(mask_right):
            continue

        x_left, y_left = x_sorted[mask_left], y_sorted[mask_left]
        x_right, y_right = x_sorted[mask_right], y_sorted[mask_right]

        # Fit linear models for each segment
        try:
            # Left segment
            if len(x_left) < 2:
                continue
            slope1, intercept1, _, _, _ = stats.linregress(x_left, y_left)

            # Right segment
            if len(x_right) < 2:
                continue
            slope2, intercept2, _, _, _ = stats.linregress(x_right, y_right)

            # Calculate residuals
            y_pred_left = slope1 * x_left + intercept1
            y_pred_right = slope2 * x_right + intercept2

            rss = np.sum((y_left - y_pred_left) ** 2) + np.sum((y_right - y_pred_right) ** 2)

            if rss < best_rss:
                best_rss = rss
                best_params = {
                    'change_point': cp,
                    'slope1': slope1,
                    'slope2': slope2,
                    'intercept1': intercept1,
                    'intercept2': intercept2,
                    'rss': rss
                }
        except Exception:
            continue

    if best_params is None:
        # Fallback to linear regression if no breakpoint found
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_sorted, y_sorted)
        rss = np.sum((y_sorted - (slope * x_sorted + intercept)) ** 2)
        return {
            'change_point': None,
            'slope1': slope,
            'slope2': slope,
            'intercept1': intercept,
            'intercept2': intercept,
            'rss': rss,
            'r_squared': r_value ** 2
        }

    # Calculate R-squared
    ss_tot = np.sum((y_sorted - np.mean(y_sorted)) ** 2)
    best_params['r_squared'] = 1 - (best_params['rss'] / ss_tot) if ss_tot > 0 else 0.0

    return best_params


def bootstrap_confidence_interval(
    data: np.ndarray,
    statistic_func,
    n_iterations: int = 1000,
    confidence_level: float = 0.95,
    random_state: Optional[int] = None
) -> Tuple[float, float, float]:
    """
    Calculate bootstrap confidence intervals for a given statistic.

    Args:
        data: Input data array.
        statistic_func: Function that computes the statistic of interest (e.g., mean, correlation).
        n_iterations: Number of bootstrap iterations.
        confidence_level: Confidence level (e.g., 0.95 for 95% CI).
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (statistic_estimate, lower_bound, upper_bound).
    """
    if random_state is not None:
        np.random.seed(random_state)

    n = len(data)
    bootstrap_stats = []

    for _ in range(n_iterations):
        # Resample with replacement
        sample = np.random.choice(data, size=n, replace=True)
        try:
            stat_val = statistic_func(sample)
            if not np.isnan(stat_val) and not np.isinf(stat_val):
                bootstrap_stats.append(stat_val)
        except Exception:
            continue

    if len(bootstrap_stats) == 0:
        raise ValueError("Bootstrap failed to compute any valid statistics.")

    bootstrap_stats = np.array(bootstrap_stats)
    estimate = statistic_func(data)
    alpha = 1 - confidence_level
    lower = np.percentile(bootstrap_stats, 100 * alpha / 2)
    upper = np.percentile(bootstrap_stats, 100 * (1 - alpha / 2))

    return float(estimate), float(lower), float(upper)


def bootstrap_correlation_ci(
    x: np.ndarray,
    y: np.ndarray,
    method: str = 'pearson',
    n_iterations: int = 1000,
    confidence_level: float = 0.95,
    random_state: Optional[int] = None
) -> Dict[str, float]:
    """
    Calculate bootstrap confidence intervals for correlation coefficients.

    Args:
        x: First variable array.
        y: Second variable array.
        method: Correlation method ('pearson' or 'spearman').
        n_iterations: Number of bootstrap iterations.
        confidence_level: Confidence level.
        random_state: Random seed.

    Returns:
        Dictionary with correlation estimate, CI bounds, and method used.
    """
    if len(x) != len(y):
        raise ValueError("Input arrays must be of equal length.")

    # Pair the data for resampling
    paired_data = np.column_stack((x, y))

    def corr_stat(paired_sample):
        xs = paired_sample[:, 0]
        ys = paired_sample[:, 1]
        if method == 'pearson':
            return pearson_correlation(xs, ys)[0]
        elif method == 'spearman':
            return spearman_correlation(xs, ys)[0]
        else:
            raise ValueError(f"Unknown method: {method}")

    estimate, lower, upper = bootstrap_confidence_interval(
        paired_data,
        corr_stat,
        n_iterations=n_iterations,
        confidence_level=confidence_level,
        random_state=random_state
    )

    return {
        'estimate': estimate,
        'lower_bound': lower,
        'upper_bound': upper,
        'confidence_level': confidence_level,
        'method': method
    }


def bootstrap_regression_ci(
    x: np.ndarray,
    y: np.ndarray,
    n_iterations: int = 1000,
    confidence_level: float = 0.95,
    random_state: Optional[int] = None
) -> Dict[str, float]:
    """
    Calculate bootstrap confidence intervals for linear regression slope.

    Args:
        x: Independent variable.
        y: Dependent variable.
        n_iterations: Number of bootstrap iterations.
        confidence_level: Confidence level.
        random_state: Random seed.

    Returns:
        Dictionary with slope estimate, CI bounds, and intercept.
    """
    if len(x) != len(y):
        raise ValueError("Input arrays must be of equal length.")

    def slope_stat(paired_sample):
        xs = paired_sample[:, 0]
        ys = paired_sample[:, 1]
        slope, intercept, _, _, _ = stats.linregress(xs, ys)
        return slope

    paired_data = np.column_stack((x, y))
    estimate, lower, upper = bootstrap_confidence_interval(
        paired_data,
        slope_stat,
        n_iterations=n_iterations,
        confidence_level=confidence_level,
        random_state=random_state
    )

    # Get the intercept for the full dataset
    _, intercept, _, _, _ = stats.linregress(x, y)

    return {
        'slope_estimate': estimate,
        'slope_lower': lower,
        'slope_upper': upper,
        'intercept': intercept,
        'confidence_level': confidence_level
    }