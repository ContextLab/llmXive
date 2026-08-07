"""
Validation module for synthetic data generation (User Story 2).

This module verifies the baseline validity of generated synthetic data,
specifically checking that shuffled (permuted) versions have ACF lag-1 ≈ 0.
This is a critical sanity check before proceeding with further analysis.
"""

import logging
import numpy as np
from typing import Dict, Any, List, Tuple
from scipy import stats

# Import from existing API surface
from src.utils.config import set_seed
from src.data.metrics import compute_acf_lag20

logger = logging.getLogger(__name__)

# Constants
ALPHA = 0.05
ACCLAG_TARGET = 0.0
ACCLAG_TOLERANCE = 0.05  # Allowable deviation from 0 for shuffled data
MIN_TRIALS = 1000  # Minimum number of shuffling trials for validation


def compute_acf_lag1(series: np.ndarray) -> float:
    """
    Compute the autocorrelation function at lag 1.

    Args:
        series: 1D numpy array of time series data.

    Returns:
        float: ACF at lag 1.
    """
    n = len(series)
    if n < 2:
        return 0.0

    mean = np.mean(series)
    var = np.var(series)

    if var == 0:
        return 0.0

    # ACF at lag 1
    acf_lag1 = np.sum((series[:-1] - mean) * (series[1:] - mean)) / ((n - 1) * var)
    return acf_lag1


def shuffle_series(series: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """
    Shuffle (permute) a time series to destroy temporal dependence.

    Args:
        series: 1D numpy array of time series data.
        rng: NumPy random generator for reproducibility.

    Returns:
        np.ndarray: Shuffled version of the series.
    """
    shuffled = series.copy()
    rng.shuffle(shuffled)
    return shuffled


def validate_shuffled_acf(
    series: np.ndarray,
    n_trials: int = MIN_TRIALS,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Validate that shuffled versions of a series have ACF lag-1 ≈ 0.

    This function performs multiple shuffling trials and checks that the
    resulting ACF lag-1 values are centered around 0, as expected for
    independent and identically distributed (i.i.d.) data.

    Args:
        series: 1D numpy array of the original time series.
        n_trials: Number of shuffling trials to perform.
        seed: Random seed for reproducibility.

    Returns:
        Dict containing validation results:
            - 'mean_acf_lag1': Mean ACF lag-1 across trials
            - 'std_acf_lag1': Standard deviation of ACF lag-1
            - 'min_acf_lag1': Minimum ACF lag-1 observed
            - 'max_acf_lag1': Maximum ACF lag-1 observed
            - 'within_tolerance': Boolean indicating if mean is within tolerance
            - 'passed': Boolean indicating if validation passed
            - 'n_trials': Number of trials performed
    """
    set_seed(seed)
    rng = np.random.default_rng(seed)

    acf_lag1_values = []

    for i in range(n_trials):
        shuffled = shuffle_series(series, rng)
        acf_lag1 = compute_acf_lag1(shuffled)
        acf_lag1_values.append(acf_lag1)

    acf_lag1_array = np.array(acf_lag1_values)

    mean_acf = np.mean(acf_lag1_array)
    std_acf = np.std(acf_lag1_array)
    min_acf = np.min(acf_lag1_array)
    max_acf = np.max(acf_lag1_array)

    # Check if mean is within tolerance of 0
    within_tolerance = abs(mean_acf) <= ACCLAG_TOLERANCE

    # Validation passes if mean ACF lag-1 is close to 0
    passed = within_tolerance

    result = {
        'mean_acf_lag1': float(mean_acf),
        'std_acf_lag1': float(std_acf),
        'min_acf_lag1': float(min_acf),
        'max_acf_lag1': float(max_acf),
        'within_tolerance': within_tolerance,
        'passed': passed,
        'n_trials': n_trials,
        'series_length': len(series),
        'seed': seed
    }

    logger.info(
        f"Shuffled ACF validation: mean={mean_acf:.6f}, "
        f"std={std_acf:.6f}, passed={passed}"
    )

    return result


def validate_baseline_hurst(
    series: np.ndarray,
    expected_h: float = 0.5,
    tolerance: float = 0.05,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Validate that white noise (H=0.5) baseline behaves as expected.

    For white noise, the Hurst exponent should be approximately 0.5.
    This function computes the DFA Hurst exponent and checks if it's
    within the specified tolerance of the expected value.

    Args:
        series: 1D numpy array of the time series (should be white noise).
        expected_h: Expected Hurst exponent (default 0.5 for white noise).
        tolerance: Acceptable deviation from expected H.
        seed: Random seed for reproducibility.

    Returns:
        Dict containing validation results:
            - 'estimated_h': Estimated Hurst exponent
            - 'expected_h': Expected Hurst exponent
            - 'deviation': Absolute deviation from expected
            - 'within_tolerance': Boolean indicating if within tolerance
            - 'passed': Boolean indicating if validation passed
    """
    set_seed(seed)

    # Import DFA computation from existing metrics module
    # Note: We're assuming the series is already processed and ready for DFA
    hurst_result = compute_dfa_hurst(series)

    estimated_h = hurst_result.get('hurst_exponent', 0.5)
    deviation = abs(estimated_h - expected_h)
    within_tolerance = deviation <= tolerance
    passed = within_tolerance

    result = {
        'estimated_h': float(estimated_h),
        'expected_h': float(expected_h),
        'deviation': float(deviation),
        'within_tolerance': within_tolerance,
        'passed': passed,
        'series_length': len(series),
        'seed': seed
    }

    logger.info(
        f"Baseline Hurst validation: estimated={estimated_h:.4f}, "
        f"expected={expected_h}, passed={passed}"
    )

    return result


def validate_synthetic_generation(
    series: np.ndarray,
    expected_h: float,
    n_shuffle_trials: int = MIN_TRIALS,
    seed: int = 42
) -> Tuple[bool, Dict[str, Any]]:
    """
    Comprehensive validation of synthetic data generation.

    This function performs multiple validation checks:
    1. Shuffled series should have ACF lag-1 ≈ 0
    2. For H=0.5, the estimated Hurst should be close to 0.5
    3. General sanity checks on the series properties

    Args:
        series: 1D numpy array of the generated synthetic series.
        expected_h: Expected Hurst exponent for the generation parameters.
        n_shuffle_trials: Number of shuffling trials for ACF validation.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (passed, results_dict):
            - passed: Boolean indicating if all validations passed
            - results_dict: Detailed results from all validation checks
    """
    set_seed(seed)

    results = {
        'series_length': len(series),
        'expected_h': expected_h,
        'seed': seed,
        'checks': {}
    }

    all_passed = True

    # Check 1: Shuffled ACF validation
    shuffle_result = validate_shuffled_acf(
        series,
        n_trials=n_shuffle_trials,
        seed=seed
    )
    results['checks']['shuffled_acf'] = shuffle_result
    if not shuffle_result['passed']:
        all_passed = False
        logger.warning(f"Shuffled ACF validation failed: {shuffle_result}")

    # Check 2: For white noise (H=0.5), validate Hurst exponent
    if abs(expected_h - 0.5) < 0.01:
        hurst_result = validate_baseline_hurst(
            series,
            expected_h=0.5,
            tolerance=0.1,  # Slightly looser tolerance for DFA
            seed=seed
        )
        results['checks']['baseline_hurst'] = hurst_result
        if not hurst_result['passed']:
            all_passed = False
            logger.warning(f"Baseline Hurst validation failed: {hurst_result}")

    # Check 3: Basic statistical properties
    mean_val = np.mean(series)
    std_val = np.std(series)

    # For fGn/ARFIMA with mean=0, check if mean is close to 0
    mean_check_passed = abs(mean_val) < 0.1 * std_val if std_val > 0 else True
    results['checks']['mean_check'] = {
        'mean': float(mean_val),
        'std': float(std_val),
        'passed': mean_check_passed
    }
    if not mean_check_passed:
        all_passed = False
        logger.warning(f"Mean check failed: mean={mean_val:.6f}, std={std_val:.6f}")

    results['overall_passed'] = all_passed

    logger.info(
        f"Synthetic generation validation complete: passed={all_passed}"
    )

    return all_passed, results


def validate_all_synthetic_series(
    series_dict: Dict[str, np.ndarray],
    h_values: Dict[str, float],
    seed: int = 42
) -> Dict[str, Any]:
    """
    Validate all generated synthetic series.

    Args:
        series_dict: Dictionary mapping series names to numpy arrays.
        h_values: Dictionary mapping series names to their expected H values.
        seed: Random seed for reproducibility.

    Returns:
        Dict containing validation results for all series:
            - 'series_results': Per-series validation results
            - 'all_passed': Boolean indicating if all series passed
            - 'failed_series': List of series names that failed
    """
    set_seed(seed)

    results = {
        'series_results': {},
        'all_passed': True,
        'failed_series': []
    }

    for series_name, series in series_dict.items():
        expected_h = h_values.get(series_name, 0.5)

        passed, validation_result = validate_synthetic_generation(
            series,
            expected_h=expected_h,
            seed=seed
        )

        results['series_results'][series_name] = {
            'passed': passed,
            'details': validation_result
        }

        if not passed:
            results['all_passed'] = False
            results['failed_series'].append(series_name)
            logger.error(f"Validation failed for series: {series_name}")

    logger.info(
        f"Validation of all synthetic series complete: "
        f"all_passed={results['all_passed']}, "
        f"failed={len(results['failed_series'])}"
    )

    return results


def main():
    """
    Main function to run validation on synthetic data.

    This function is intended to be run as a script to validate
    the synthetic data generation pipeline before proceeding with
    further analysis.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting synthetic data validation...")

    # Example: Create a simple white noise series for demonstration
    # In practice, this would load from the actual generated synthetic data
    set_seed(42)
    rng = np.random.default_rng(42)

    # Generate white noise (H=0.5)
    n_points = 1000
    white_noise = rng.standard_normal(n_points)

    # Validate the white noise series
    passed, results = validate_synthetic_generation(
        white_noise,
        expected_h=0.5,
        n_shuffle_trials=1000,
        seed=42
    )

    logger.info(f"White noise validation: passed={passed}")
    logger.info(f"Results: {results}")

    if not passed:
        logger.error("VALIDATION FAILED - Blocking further analysis")
        return 1

    logger.info("VALIDATION PASSED - Safe to proceed with analysis")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
