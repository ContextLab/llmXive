"""
Correlation analysis module for investigating gut microbiome and cognitive flexibility.

This module performs Pearson and Spearman correlations with automatic switching
based on distributional properties (skewness and Shapiro-Wilk test).
It also handles Benjamini-Hochberg correction for multiple comparisons.
"""

import logging
import sys
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List, Union
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests

from code.src.utils.config import (
    get_project_root,
    get_results_dir,
    get_logs_dir,
    SEED
)

# Set random seed for reproducibility
np.random.seed(SEED)

# Configure logging
LOGS_DIR = get_logs_dir()
LOGS_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'correlation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def calculate_skewness(series: pd.Series) -> float:
    """
    Calculate the skewness of a series.

    Args:
        series: Input pandas Series.

    Returns:
        Skewness value.
    """
    return series.skew()


def shapiro_wilk_test(series: pd.Series) -> Tuple[float, float]:
    """
    Perform Shapiro-Wilk test for normality.

    Args:
        series: Input pandas Series.

    Returns:
        Tuple of (statistic, p-value).
    """
    # Shapiro-Wilk has a limit on sample size (n <= 5000)
    n = len(series.dropna())
    if n > 5000:
        logger.warning(f"Sample size {n} exceeds Shapiro-Wilk limit (5000). Using subsample.")
        sample = series.dropna().sample(n=5000, random_state=SEED)
        return stats.shapiro(sample)
    elif n < 3:
        logger.warning("Sample size too small for Shapiro-Wilk test.")
        return 0.0, 1.0
    return stats.shapiro(series.dropna())


def should_switch_to_spearman(
    x: pd.Series,
    y: pd.Series,
    skewness_threshold: float = 1.0,
    shapiro_p_threshold: float = 0.05
) -> bool:
    """
    Determine if we should switch from Pearson to Spearman correlation.

    Switch conditions:
    1. Skewness of either variable > threshold
    2. Shapiro-Wilk p-value < threshold for either variable

    Args:
        x: First variable series.
        y: Second variable series.
        skewness_threshold: Maximum allowed skewness before switching.
        shapiro_p_threshold: Minimum p-value for normality before switching.

    Returns:
        True if Spearman should be used, False otherwise.
    """
    # Check skewness
    skew_x = calculate_skewness(x)
    skew_y = calculate_skewness(y)

    logger.info(f"Skewness check - X: {skew_x:.4f}, Y: {skew_y:.4f} (threshold: {skewness_threshold})")

    if abs(skew_x) > skewness_threshold or abs(skew_y) > skewness_threshold:
        logger.info(f"Switching to Spearman: skewness exceeded threshold ({abs(skew_x):.4f}, {abs(skew_y):.4f})")
        return True

    # Check normality with Shapiro-Wilk
    try:
        _, p_x = shapiro_wilk_test(x)
        _, p_y = shapiro_wilk_test(y)

        logger.info(f"Shapiro-Wilk p-values - X: {p_x:.4f}, Y: {p_y:.4f} (threshold: {shapiro_p_threshold})")

        if p_x < shapiro_p_threshold or p_y < shapiro_p_threshold:
            logger.info(f"Switching to Spearman: normality assumption violated (p_x={p_x:.4f}, p_y={p_y:.4f})")
            return True

    except Exception as e:
        logger.warning(f"Shapiro-Wilk test failed: {e}. Switching to Spearman.")
        return True

    return False


def pearson_correlation_with_ci(
    x: pd.Series,
    y: pd.Series,
    confidence_level: float = 0.95
) -> Dict[str, Any]:
    """
    Calculate Pearson correlation with confidence interval.

    Args:
        x: First variable series.
        y: Second variable series.
        confidence_level: Confidence level for interval (default 0.95).

    Returns:
        Dictionary with correlation coefficient, p-value, and confidence interval.
    """
    # Remove NaN values
    mask = x.notna() & y.notna()
    x_clean = x[mask]
    y_clean = y[mask]

    if len(x_clean) < 2:
        logger.warning("Insufficient data points for correlation.")
        return {
            'correlation_coefficient': np.nan,
            'p_value': np.nan,
            'confidence_interval': (np.nan, np.nan),
            'n': len(x_clean)
        }

    # Calculate Pearson correlation
    corr, p_val = stats.pearsonr(x_clean, y_clean)

    # Calculate confidence interval using Fisher transformation
    n = len(x_clean)
    if abs(corr) >= 1.0:
        # Perfect correlation - CI is just the point
        ci_lower = ci_upper = corr
    else:
        # Fisher z-transformation
        z = np.arctanh(corr)
        se = 1.0 / np.sqrt(n - 3)
        z_critical = stats.norm.ppf(1 - (1 - confidence_level) / 2)

        z_lower = z - z_critical * se
        z_upper = z + z_critical * se

        ci_lower = np.tanh(z_lower)
        ci_upper = np.tanh(z_upper)

    return {
        'correlation_coefficient': corr,
        'p_value': p_val,
        'confidence_interval': (ci_lower, ci_upper),
        'n': n
    }


def spearman_correlation_with_ci(
    x: pd.Series,
    y: pd.Series,
    confidence_level: float = 0.95
) -> Dict[str, Any]:
    """
    Calculate Spearman correlation with confidence interval (bootstrap).

    Args:
        x: First variable series.
        y: Second variable series.
        confidence_level: Confidence level for interval (default 0.95).

    Returns:
        Dictionary with correlation coefficient, p-value, and confidence interval.
    """
    mask = x.notna() & y.notna()
    x_clean = x[mask]
    y_clean = y[mask]

    if len(x_clean) < 2:
        logger.warning("Insufficient data points for correlation.")
        return {
            'correlation_coefficient': np.nan,
            'p_value': np.nan,
            'confidence_interval': (np.nan, np.nan),
            'n': len(x_clean)
        }

    # Calculate Spearman correlation
    corr, p_val = stats.spearmanr(x_clean, y_clean)

    # Bootstrap confidence interval for Spearman
    n_bootstrap = 1000
    bootstrap_corrs = []

    for _ in range(n_bootstrap):
        indices = np.random.choice(len(x_clean), size=len(x_clean), replace=True)
        boot_x = x_clean.iloc[indices]
        boot_y = y_clean.iloc[indices]
        boot_corr, _ = stats.spearmanr(boot_x, boot_y)
        bootstrap_corrs.append(boot_corr)

    ci_lower = np.percentile(bootstrap_corrs, (1 - confidence_level) / 2 * 100)
    ci_upper = np.percentile(bootstrap_corrs, (1 + confidence_level) / 2 * 100)

    return {
        'correlation_coefficient': corr,
        'p_value': p_val,
        'confidence_interval': (ci_lower, ci_upper),
        'n': len(x_clean)
    }


def apply_benjamini_hochberg(p_values: pd.Series) -> pd.Series:
    """
    Apply Benjamini-Hochberg correction for multiple comparisons.

    Args:
        p_values: Series of p-values.

    Returns:
        Series of adjusted p-values.
    """
    # multipletests returns (reject, p_adjusted, p_lower, p_upper)
    # We only need the adjusted p-values
    _, p_adjusted, _, _ = multipletests(p_values, method='fdr_bh')
    return pd.Series(p_adjusted, index=p_values.index)


def run_correlation_analysis(
    data: pd.DataFrame,
    diversity_col: str,
    cognitive_col: str,
    covariates: Optional[List[str]] = None,
    skewness_threshold: float = 1.0,
    shapiro_p_threshold: float = 0.05,
    confidence_level: float = 0.95
) -> Dict[str, Any]:
    """
    Run correlation analysis between diversity metric and cognitive score.

    Automatically switches between Pearson and Spearman based on distribution.

    Args:
        data: DataFrame containing the variables.
        diversity_col: Name of the diversity metric column.
        cognitive_col: Name of the cognitive score column.
        covariates: Optional list of covariate column names.
        skewness_threshold: Threshold for skewness check.
        shapiro_p_threshold: Threshold for Shapiro-Wilk test.
        confidence_level: Confidence level for intervals.

    Returns:
        Dictionary with correlation results.
    """
    logger.info(f"Starting correlation analysis: {diversity_col} vs {cognitive_col}")

    x = data[diversity_col]
    y = data[cognitive_col]

    # Determine correlation method
    use_spearman = should_switch_to_spearman(
        x, y, skewness_threshold, shapiro_p_threshold
    )

    method = "Spearman" if use_spearman else "Pearson"
    logger.info(f"Using {method} correlation")

    # Calculate correlation
    if use_spearman:
        result = spearman_correlation_with_ci(x, y, confidence_level)
    else:
        result = pearson_correlation_with_ci(x, y, confidence_level)

    result['method'] = method
    result['diversity_variable'] = diversity_col
    result['cognitive_variable'] = cognitive_col

    # Log the switch decision
    if use_spearman:
        logger.info(f"Switched to Spearman for {diversity_col} vs {cognitive_col}")
    else:
        logger.info(f"Used Pearson for {diversity_col} vs {cognitive_col}")

    return result


def run_multiple_correlations(
    data: pd.DataFrame,
    diversity_cols: List[str],
    cognitive_col: str,
    skewness_threshold: float = 1.0,
    shapiro_p_threshold: float = 0.05,
    confidence_level: float = 0.95
) -> pd.DataFrame:
    """
    Run correlation analysis for multiple diversity metrics.

    Args:
        data: DataFrame containing the variables.
        diversity_cols: List of diversity metric column names.
        cognitive_col: Name of the cognitive score column.
        skewness_threshold: Threshold for skewness check.
        shapiro_p_threshold: Threshold for Shapiro-Wilk test.
        confidence_level: Confidence level for intervals.

    Returns:
        DataFrame with correlation results for all diversity metrics.
    """
    results = []

    for div_col in diversity_cols:
        logger.info(f"Analyzing {div_col} vs {cognitive_col}")
        result = run_correlation_analysis(
            data, div_col, cognitive_col,
            skewness_threshold, shapiro_p_threshold, confidence_level
        )
        results.append(result)

    results_df = pd.DataFrame(results)

    # Apply Benjamini-Hochberg correction
    if len(results_df) > 1:
        results_df['adjusted_p_value'] = apply_benjamini_hochberg(results_df['p_value'])
    else:
        results_df['adjusted_p_value'] = results_df['p_value']

    logger.info("Benjamini-Hochberg correction applied")

    return results_df


def main():
    """
    Main function to run correlation analysis on filtered cohort data.
    """
    logger.info("Starting correlation analysis pipeline")

    # Load filtered cohort data
    processed_dir = get_project_root() / "code" / "data" / "processed"
    filtered_cohort_path = processed_dir / "filtered_cohort.csv"

    if not filtered_cohort_path.exists():
        logger.error(f"Filtered cohort not found at {filtered_cohort_path}")
        logger.info("Please run data ingestion and filtering first")
        return

    data = pd.read_csv(filtered_cohort_path)
    logger.info(f"Loaded {len(data)} participants from filtered cohort")

    # Define diversity metrics and cognitive score
    diversity_cols = ['shannon', 'simpson', 'chao1']
    cognitive_col = 'cognitive_flexibility_score'

    # Check if required columns exist
    missing_cols = [col for col in diversity_cols + [cognitive_col] if col not in data.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return

    # Run correlation analysis
    results_df = run_multiple_correlations(
        data,
        diversity_cols,
        cognitive_col,
        skewness_threshold=1.0,
        shapiro_p_threshold=0.05,
        confidence_level=0.95
    )

    # Save results
    results_dir = get_results_dir()
    output_path = results_dir / "correlation_results.json"

    # Convert DataFrame to list of dicts for JSON serialization
    results_list = results_df.to_dict(orient='records')

    # Ensure confidence intervals are serializable (convert tuples to lists)
    for result in results_list:
        if 'confidence_interval' in result and isinstance(result['confidence_interval'], tuple):
            result['confidence_interval'] = list(result['confidence_interval'])

    import json
    with open(output_path, 'w') as f:
        json.dump(results_list, f, indent=2)

    logger.info(f"Correlation results saved to {output_path}")
    logger.info("Correlation analysis completed successfully")

    # Print summary
    print("\nCorrelation Analysis Summary:")
    print("-" * 60)
    print(f"{'Variable':<20} {'Method':<10} {'r':<10} {'p-value':<10} {'Adj. p':<10}")
    print("-" * 60)
    for _, row in results_df.iterrows():
        print(f"{row['diversity_variable']:<20} {row['method']:<10} {row['correlation_coefficient']:.4f} "
              f"{row['p_value']:.4f} {row['adjusted_p_value']:.4f}")
    print("-" * 60)


if __name__ == "__main__":
    main()