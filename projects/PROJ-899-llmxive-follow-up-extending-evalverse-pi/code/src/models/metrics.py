"""
Metrics module for correlation analysis and sensitivity testing.
Implements Pearson/Spearman correlation, bootstrapping, and threshold sweeps.
"""
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from scipy import stats
import pandas as pd
import os
from src.utils import get_logger, write_csv, ensure_directories
from src.config import get_data_root

logger = get_logger(__name__)

def pearson_correlation(x: List[float], y: List[float]) -> float:
    """
    Calculate Pearson correlation coefficient.

    Args:
        x: First variable
        y: Second variable

    Returns:
        Pearson correlation coefficient (r)
    """
    if len(x) != len(y) or len(x) < 2:
        return 0.0

    x_arr = np.array(x)
    y_arr = np.array(y)

    # Handle constant arrays
    if np.std(x_arr) == 0 or np.std(y_arr) == 0:
        return 0.0

    return float(stats.pearsonr(x_arr, y_arr)[0])

def spearman_correlation(x: List[float], y: List[float]) -> float:
    """
    Calculate Spearman rank correlation coefficient.

    Args:
        x: First variable
        y: Second variable

    Returns:
        Spearman correlation coefficient (rho)
    """
    if len(x) != len(y) or len(x) < 2:
        return 0.0

    x_arr = np.array(x)
    y_arr = np.array(y)

    # Handle constant arrays
    if np.std(x_arr) == 0 or np.std(y_arr) == 0:
        return 0.0

    return float(stats.spearmanr(x_arr, y_arr)[0])

def bootstrap_confidence_interval(
    x: List[float],
    y: List[float],
    correlation_func,
    n_bootstrap: int = 1000,
    confidence_level: float = 0.95,
    random_seed: int = 42
) -> Tuple[float, float, float]:
    """
    Calculate bootstrap confidence interval for correlation.

    Args:
        x: First variable
        y: Second variable
        correlation_func: Function to calculate correlation (pearson or spearman)
        n_bootstrap: Number of bootstrap iterations
        confidence_level: Confidence level (default 0.95)
        random_seed: Random seed for reproducibility

    Returns:
        Tuple of (correlation, lower_ci, upper_ci)
    """
    if len(x) != len(y) or len(x) < 2:
        return 0.0, 0.0, 0.0

    np.random.seed(random_seed)
    n = len(x)
    correlations = []

    for _ in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(n, size=n, replace=True)
        x_sample = [x[i] for i in indices]
        y_sample = [y[i] for i in indices]

        corr = correlation_func(x_sample, y_sample)
        if not np.isnan(corr):
            correlations.append(corr)

    if not correlations:
        return 0.0, 0.0, 0.0

    correlations = np.array(correlations)
    corr_estimate = np.mean(correlations)
    alpha = 1 - confidence_level
    lower_ci = np.percentile(correlations, 100 * alpha / 2)
    upper_ci = np.percentile(correlations, 100 * (1 - alpha / 2))

    return float(corr_estimate), float(lower_ci), float(upper_ci)

def run_threshold_sweep(
    dimensions_data: Dict[str, Dict[str, Any]],
    thresholds: List[float] = [0.80, 0.85, 0.90],
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Run threshold sweep analysis for dimension classification.

    Args:
        dimensions_data: Dictionary mapping dimension names to their stats
        thresholds: List of thresholds to test
        output_path: Path to save raw sweep results

    Returns:
        DataFrame with raw classification outcomes
    """
    results = []

    for dim_name, stats in dimensions_data.items():
        r_value = stats.get('pearson_r', 0.0)
        lower_ci = stats.get('lower_ci', 0.0)

        for threshold in thresholds:
            # Determine status based on threshold
            if r_value >= threshold:
                status = "feature_sufficient"
            elif lower_ci < 0.70:
                status = "vlm_required"
            else:
                status = "inconclusive"

            results.append({
                "dimension": dim_name,
                "threshold": threshold,
                "status": status,
                "pearson_r": r_value,
                "lower_ci": lower_ci
            })

    df = pd.DataFrame(results)

    if output_path is None:
        output_path = os.path.join(get_data_root(), "sensitivity_sweep_raw.csv")

    ensure_directories(output_path)
    write_csv(df, output_path)
    logger.info(f"Saved threshold sweep results to: {output_path}")

    return df

def calculate_dimension_metrics(
    predictions: List[float],
    actuals: List[float],
    n_bootstrap: int = 1000
) -> Dict[str, float]:
    """
    Calculate comprehensive metrics for a dimension.

    Args:
        predictions: Model predictions
        actuals: Human expert scores
        n_bootstrap: Number of bootstrap iterations

    Returns:
        Dictionary with correlation metrics and CIs
    """
    pearson_r = pearson_correlation(predictions, actuals)
    spearman_rho = spearman_correlation(predictions, actuals)

    pearson_lower, pearson_upper = bootstrap_confidence_interval(
        predictions, actuals, pearson_correlation, n_bootstrap
    )[1:]

    spearman_lower, spearman_upper = bootstrap_confidence_interval(
        predictions, actuals, spearman_correlation, n_bootstrap
    )[1:]

    return {
        "pearson_r": pearson_r,
        "pearson_lower_ci": pearson_lower,
        "pearson_upper_ci": pearson_upper,
        "spearman_rho": spearman_rho,
        "spearman_lower_ci": spearman_lower,
        "spearman_upper_ci": spearman_upper
    }
