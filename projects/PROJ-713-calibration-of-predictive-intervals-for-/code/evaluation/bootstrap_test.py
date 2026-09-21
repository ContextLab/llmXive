"""
Bootstrap test module for statistical significance of coverage deviations.

Implements paired bootstrap tests to compare predictive interval coverage
between different models at the time-series level.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from scipy import stats
from utils.logger import get_logger
from utils.exceptions import CalibrationError, DataValidationError

logger = get_logger(__name__)


def paired_bootstrap_test(
    coverage_deviations_model_a: np.ndarray,
    coverage_deviations_model_b: np.ndarray,
    n_resamples: int = 1000,
    alpha: float = 0.05,
    random_seed: Optional[int] = None
) -> Dict[str, Union[float, bool, int]]:
    """
    Perform a paired bootstrap test to compare coverage deviations between two models.

    The test assesses whether the mean difference in coverage deviations between
    two models is statistically significant.

    Args:
        coverage_deviations_model_a: Array of coverage deviations (empirical - nominal) for model A.
        coverage_deviations_model_b: Array of coverage deviations (empirical - nominal) for model B.
        n_resamples: Number of bootstrap resamples (default: 1000).
        alpha: Significance level (default: 0.05).
        random_seed: Random seed for reproducibility.

    Returns:
        Dictionary containing:
            - 'mean_diff': Mean difference (Model A - Model B)
            - 'bootstrap_mean_diff': Mean of bootstrap distribution of differences
            - 'ci_lower': Lower bound of 95% confidence interval
            - 'ci_upper': Upper bound of 95% confidence interval
            - 'p_value': Two-sided p-value from bootstrap test
            - 'significant': Boolean indicating if p_value < alpha
            - 'n_resamples': Number of resamples performed
    """
    if len(coverage_deviations_model_a) != len(coverage_deviations_model_b):
        raise DataValidationError(
            f"Coverage deviation arrays must have the same length. "
            f"Got {len(coverage_deviations_model_a)} and {len(coverage_deviations_model_b)}"
        )

    if len(coverage_deviations_model_a) == 0:
        raise DataValidationError("Coverage deviation arrays cannot be empty.")

    if random_seed is not None:
        np.random.seed(random_seed)

    # Calculate observed mean difference
    differences = coverage_deviations_model_a - coverage_deviations_model_b
    observed_mean_diff = np.mean(differences)

    # Bootstrap resampling
    bootstrap_means = []
    n_series = len(differences)

    for _ in range(n_resamples):
        # Resample with replacement at the series level
        indices = np.random.choice(n_series, size=n_series, replace=True)
        resampled_diffs = differences[indices]
        bootstrap_means.append(np.mean(resampled_diffs))

    bootstrap_means = np.array(bootstrap_means)

    # Calculate confidence interval (percentile method)
    ci_lower = np.percentile(bootstrap_means, (alpha / 2) * 100)
    ci_upper = np.percentile(bootstrap_means, (1 - alpha / 2) * 100)

    # Calculate two-sided p-value
    # Count how many bootstrap means are as extreme or more extreme than observed
    # under the null hypothesis that the true difference is zero
    # We center the bootstrap distribution at zero for the null hypothesis
    centered_bootstrap = bootstrap_means - np.mean(bootstrap_means)
    extreme_count = np.sum(np.abs(centered_bootstrap) >= np.abs(observed_mean_diff))
    p_value = extreme_count / n_resamples

    result = {
        'mean_diff': float(observed_mean_diff),
        'bootstrap_mean_diff': float(np.mean(bootstrap_means)),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'p_value': float(p_value),
        'significant': bool(p_value < alpha),
        'n_resamples': n_resamples
    }

    logger.info(
        f"Bootstrap test completed: mean_diff={observed_mean_diff:.4f}, "
        f"p_value={p_value:.4f}, significant={p_value < alpha}"
    )

    return result


def compare_models_coverage(
    results_df: pd.DataFrame,
    model_a: str,
    model_b: str,
    nominal_level: float,
    n_resamples: int = 1000,
    alpha: float = 0.05,
    random_seed: Optional[int] = None
) -> Dict[str, Union[float, bool, int, str]]:
    """
    Compare coverage deviations between two specific models for a given nominal level.

    Args:
        results_df: DataFrame containing coverage results with columns:
                    'series_id', 'model', 'nominal_level', 'empirical_coverage', 'deviation'
        model_a: Name of the first model to compare.
        model_b: Name of the second model to compare.
        nominal_level: The confidence level (e.g., 0.80, 0.95) to compare.
        n_resamples: Number of bootstrap resamples.
        alpha: Significance level.
        random_seed: Random seed for reproducibility.

    Returns:
        Dictionary containing test results and metadata.
    """
    # Filter data for the two models and specified nominal level
    mask = (
        (results_df['model'].isin([model_a, model_b])) &
        (results_df['nominal_level'] == nominal_level)
    )
    filtered_df = results_df[mask]

    if len(filtered_df) == 0:
        raise DataValidationError(
            f"No data found for models {model_a} and {model_b} at nominal level {nominal_level}"
        )

    # Extract deviations for each model
    deviations_a = filtered_df[filtered_df['model'] == model_a]['deviation'].values
    deviations_b = filtered_df[filtered_df['model'] == model_b]['deviation'].values

    if len(deviations_a) != len(deviations_b):
        # In case of missing series for one model, we need to handle this
        # For paired test, we should only include series present in both
        logger.warning(
            f"Unequal number of series: {model_a} has {len(deviations_a)}, "
            f"{model_b} has {len(deviations_b)}. Filtering to common series."
        )
        # This assumes series_id is the key for pairing
        common_series = set(filtered_df[filtered_df['model'] == model_a]['series_id']) & \
                        set(filtered_df[filtered_df['model'] == model_b]['series_id'])
        
        deviations_a = filtered_df[
            (filtered_df['model'] == model_a) & 
            (filtered_df['series_id'].isin(common_series))
        ]['deviation'].values
        
        deviations_b = filtered_df[
            (filtered_df['model'] == model_b) & 
            (filtered_df['series_id'].isin(common_series))
        ]['deviation'].values

    if len(deviations_a) == 0:
        raise DataValidationError(
            f"No common series found between {model_a} and {model_b} for nominal level {nominal_level}"
        )

    logger.info(
        f"Running bootstrap test for {model_a} vs {model_b} at level {nominal_level} "
        f"with {len(deviations_a)} series"
    )

    test_result = paired_bootstrap_test(
        deviations_a,
        deviations_b,
        n_resamples=n_resamples,
        alpha=alpha,
        random_seed=random_seed
    )

    return {
        'model_a': model_a,
        'model_b': model_b,
        'nominal_level': nominal_level,
        'n_series': len(deviations_a),
        **test_result
    }


def run_all_pairwise_comparisons(
    results_df: pd.DataFrame,
    models: List[str],
    nominal_levels: List[float],
    n_resamples: int = 1000,
    alpha: float = 0.05,
    random_seed: Optional[int] = None
) -> List[Dict[str, Union[float, bool, int, str]]]:
    """
    Run pairwise bootstrap tests for all model combinations across all nominal levels.

    Args:
        results_df: DataFrame containing coverage results.
        models: List of model names to compare.
        nominal_levels: List of nominal confidence levels to test.
        n_resamples: Number of bootstrap resamples.
        alpha: Significance level.
        random_seed: Random seed for reproducibility.

    Returns:
        List of dictionaries, each containing results for one comparison.
    """
    all_results = []

    # Generate all unique pairs
    from itertools import combinations
    model_pairs = list(combinations(models, 2))

    for model_a, model_b in model_pairs:
        for level in nominal_levels:
            try:
                result = compare_models_coverage(
                    results_df,
                    model_a,
                    model_b,
                    level,
                    n_resamples=n_resamples,
                    alpha=alpha,
                    random_seed=random_seed
                )
                all_results.append(result)
            except DataValidationError as e:
                logger.warning(f"Skipping comparison {model_a} vs {model_b} at level {level}: {e}")
            except Exception as e:
                logger.error(f"Error in comparison {model_a} vs {model_b} at level {level}: {e}")
                raise

    return all_results


def aggregate_bootstrap_results(
    comparison_results: List[Dict[str, Union[float, bool, int, str]]],
    output_path: str
) -> pd.DataFrame:
    """
    Aggregate bootstrap test results and save to CSV.

    Args:
        comparison_results: List of result dictionaries from run_all_pairwise_comparisons.
        output_path: Path to save the CSV file.

    Returns:
        DataFrame containing all results.
    """
    if not comparison_results:
        raise DataValidationError("No comparison results to aggregate.")

    df = pd.DataFrame(comparison_results)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} bootstrap comparison results to {output_path}")

    return df