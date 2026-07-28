"""
Bootstrap significance testing for predictive interval calibration.

This module implements paired bootstrap tests to compare coverage deviations
between different forecasting models (ARIMA, Prophet, LSTM) on the same
time series data.

The test uses time-series level resampling to preserve autocorrelation structure
within blocks while allowing variation between series.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from scipy import stats
from utils.logger import get_logger
from utils.exceptions import CalibrationError, DataValidationError

logger = get_logger(__name__)


def paired_bootstrap_test(
    coverage_deviation_model_a: Union[np.ndarray, List[float]],
    coverage_deviation_model_b: Union[np.ndarray, List[float]],
    n_resamples: int = 1000,
    alpha: float = 0.05,
    random_seed: Optional[int] = None
) -> Dict[str, float]:
    """
    Perform a paired bootstrap test to compare coverage deviations between two models.

    The null hypothesis is that there is no difference in the mean coverage deviation
    between the two models. The alternative is that they differ (two-sided test).

    Args:
        coverage_deviation_model_a: Array of coverage deviations for model A
            (empirical_coverage - nominal_coverage) for each series.
        coverage_deviation_model_b: Array of coverage deviations for model B.
        n_resamples: Number of bootstrap resamples to generate.
        alpha: Significance level for the test (default 0.05).
        random_seed: Random seed for reproducibility.

    Returns:
        Dictionary containing:
            - 'p_value': Two-sided p-value from the bootstrap test.
            - 'mean_diff_a': Mean coverage deviation for model A.
            - 'mean_diff_b': Mean coverage deviation for model B.
            - 'observed_diff': Observed difference (mean_a - mean_b).
            - 'significant': Boolean indicating if p_value < alpha.
            - 'confidence_interval': 95% CI for the difference in means.

    Raises:
        DataValidationError: If input arrays have different lengths or are empty.
        CalibrationError: If bootstrap computation fails.
    """
    dev_a = np.asarray(coverage_deviation_model_a, dtype=float)
    dev_b = np.asarray(coverage_deviation_model_b, dtype=float)

    if len(dev_a) == 0 or len(dev_b) == 0:
        raise DataValidationError("Coverage deviation arrays cannot be empty.")

    if len(dev_a) != len(dev_b):
        raise DataValidationError(
            f"Coverage deviation arrays must have same length. "
            f"Got {len(dev_a)} and {len(dev_b)}."
        )

    if random_seed is not None:
        np.random.seed(random_seed)

    # Observed difference in means
    mean_a = np.mean(dev_a)
    mean_b = np.mean(dev_b)
    observed_diff = mean_a - mean_b

    # Paired bootstrap: resample indices and compute difference of means
    n = len(dev_a)
    bootstrap_diffs = np.empty(n_resamples)

    try:
        for i in range(n_resamples):
            indices = np.random.choice(n, size=n, replace=True)
            resampled_a = dev_a[indices]
            resampled_b = dev_b[indices]
            bootstrap_diffs[i] = np.mean(resampled_a) - np.mean(resampled_b)

    except Exception as e:
        raise CalibrationError(f"Bootstrap resampling failed: {e}")

    # Two-sided p-value: proportion of bootstrap diffs with |diff| >= |observed|
    abs_observed = np.abs(observed_diff)
    p_value = np.mean(np.abs(bootstrap_diffs) >= abs_observed)

    # Confidence interval for the difference (percentile method)
    lower_ci = np.percentile(bootstrap_diffs, 100 * alpha / 2)
    upper_ci = np.percentile(bootstrap_diffs, 100 * (1 - alpha / 2))

    return {
        'p_value': float(p_value),
        'mean_diff_a': float(mean_a),
        'mean_diff_b': float(mean_b),
        'observed_diff': float(observed_diff),
        'significant': bool(p_value < alpha),
        'confidence_interval': (float(lower_ci), float(upper_ci)),
        'n_resamples': n_resamples,
        'n_series': n
    }


def compare_models_coverage(
    results_df: pd.DataFrame,
    model_a: str,
    model_b: str,
    confidence_level: float,
    n_resamples: int = 1000,
    alpha: float = 0.05,
    random_seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Compare coverage deviations between two models for a specific confidence level.

    Args:
        results_df: DataFrame containing coverage results with columns:
            - 'model': Model name
            - 'confidence_level': Nominal confidence level
            - 'coverage_deviation': Deviation from nominal coverage
        model_a: Name of the first model to compare.
        model_b: Name of the second model to compare.
        confidence_level: The confidence level to filter results (e.g., 0.80, 0.95).
        n_resamples: Number of bootstrap resamples.
        alpha: Significance level.
        random_seed: Random seed.

    Returns:
        Dictionary with test results for the specified models and confidence level.

    Raises:
        DataValidationError: If required columns are missing or data is insufficient.
    """
    required_cols = ['model', 'confidence_level', 'coverage_deviation']
    missing_cols = [c for c in required_cols if c not in results_df.columns]
    if missing_cols:
        raise DataValidationError(
            f"Results DataFrame missing required columns: {missing_cols}"
        )

    # Filter for the specified confidence level
    mask = results_df['confidence_level'] == confidence_level
    subset = results_df[mask]

    if len(subset) == 0:
        raise DataValidationError(
            f"No results found for confidence_level={confidence_level}"
        )

    # Get deviations for each model
    dev_a = subset[subset['model'] == model_a]['coverage_deviation'].values
    dev_b = subset[subset['model'] == model_b]['coverage_deviation'].values

    if len(dev_a) == 0 or len(dev_b) == 0:
        raise DataValidationError(
            f"Insufficient data for comparison. "
            f"Model A ({model_a}): {len(dev_a)} series, "
            f"Model B ({model_b}): {len(dev_b)} series."
        )

    # Run paired bootstrap test
    test_result = paired_bootstrap_test(
        dev_a,
        dev_b,
        n_resamples=n_resamples,
        alpha=alpha,
        random_seed=random_seed
    )

    test_result['model_a'] = model_a
    test_result['model_b'] = model_b
    test_result['confidence_level'] = confidence_level

    logger.info(
        f"Bootstrap test: {model_a} vs {model_b} at {confidence_level:.2f} "
        f"(p={test_result['p_value']:.4f}, significant={test_result['significant']})"
    )

    return test_result


def run_all_pairwise_comparisons(
    results_df: pd.DataFrame,
    models: List[str],
    confidence_levels: List[float],
    n_resamples: int = 1000,
    alpha: float = 0.05,
    random_seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Run pairwise bootstrap tests for all model combinations and confidence levels.

    Args:
        results_df: DataFrame with coverage results.
        models: List of model names to compare.
        confidence_levels: List of confidence levels to test.
        n_resamples: Number of bootstrap resamples per test.
        alpha: Significance level.
        random_seed: Random seed.

    Returns:
        DataFrame with one row per model pair and confidence level, containing
        test statistics and p-values.
    """
    results = []

    for cl in confidence_levels:
        for i, model_a in enumerate(models):
            for model_b in models[i+1:]:
                try:
                    test_result = compare_models_coverage(
                        results_df,
                        model_a,
                        model_b,
                        cl,
                        n_resamples,
                        alpha,
                        random_seed
                    )
                    results.append(test_result)
                except (DataValidationError, CalibrationError) as e:
                    logger.warning(
                        f"Skipping comparison {model_a} vs {model_b} at {cl}: {e}"
                    )
                    continue

    if not results:
        return pd.DataFrame()

    return pd.DataFrame(results)


def aggregate_bootstrap_results(
    results_df: pd.DataFrame,
    models: List[str],
    confidence_levels: List[float],
    output_path: str,
    n_resamples: int = 1000,
    alpha: float = 0.05,
    random_seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Run all pairwise comparisons and save results to CSV.

    Args:
        results_df: DataFrame with coverage results.
        models: List of model names.
        confidence_levels: List of confidence levels.
        output_path: Path to save the results CSV.
        n_resamples: Number of bootstrap resamples.
        alpha: Significance level.
        random_seed: Random seed.

    Returns:
        DataFrame with all test results.
    """
    comparison_df = run_all_pairwise_comparisons(
        results_df,
        models,
        confidence_levels,
        n_resamples,
        alpha,
        random_seed
    )

    if not comparison_df.empty:
        comparison_df.to_csv(output_path, index=False)
        logger.info(f"Saved bootstrap comparison results to {output_path}")
    else:
        logger.warning("No comparisons were successful; no output file created.")

    return comparison_df
