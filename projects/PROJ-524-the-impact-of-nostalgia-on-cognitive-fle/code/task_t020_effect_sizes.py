"""
Task T020: Effect Size Calculation

Calculates Cohen's d with 95% confidence intervals for primary comparisons
(perseverative_errors and categories_completed) between nostalgia and control groups.
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from scipy import stats

from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

# Configure logging
logger = setup_logging()

def load_cleaned_dataset() -> pd.DataFrame:
    """Load the cleaned dataset from the processed directory."""
    path = Path("data/processed/cleaned_dataset.csv")
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    return pd.read_csv(path)

def calculate_cohen_d(group1: np.ndarray, group2: np.ndarray) -> Tuple[float, float, float]:
    """
    Calculate Cohen's d effect size and 95% confidence interval.

    Args:
        group1: Array of values for group 1 (e.g., nostalgia)
        group2: Array of values for group 2 (e.g., control)

    Returns:
        Tuple of (cohens_d, ci_lower, ci_upper)
    """
    n1, n2 = len(group1), len(group2)
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)

    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

    if pooled_std == 0:
        log_warning("Pooled standard deviation is zero; Cohen's d is undefined.")
        return 0.0, 0.0, 0.0

    cohens_d = (mean1 - mean2) / pooled_std

    # Calculate 95% CI for Cohen's d
    # Using non-central t-distribution approximation
    # Standard error of Cohen's d
    se_d = np.sqrt((n1 + n2) / (n1 * n2) + (cohens_d ** 2) / (2 * (n1 + n2)))

    # 95% CI
    z = 1.96  # Approximation for 95% CI
    ci_lower = cohens_d - z * se_d
    ci_upper = cohens_d + z * se_d

    return cohens_d, ci_lower, ci_upper

def calculate_effect_sizes(df: pd.DataFrame, metric: str, group_col: str = "stimulus_type") -> Dict[str, Any]:
    """
    Calculate effect sizes for a specific metric between two groups.

    Args:
        df: Cleaned dataframe
        metric: Column name for the metric (e.g., 'perseverative_errors')
        group_col: Column name defining groups (default: 'stimulus_type')

    Returns:
        Dictionary with effect size results
    """
    if metric not in df.columns:
        raise ValueError(f"Metric column '{metric}' not found in dataframe")

    # Filter out rows with missing values
    valid_df = df[[metric, group_col]].dropna()

    # Ensure we have both groups
    groups = valid_df[group_col].unique()
    if len(groups) < 2:
        log_warning(f"Only one group found ({groups}); cannot calculate effect size.")
        return {
            "metric": metric,
            "cohens_d": None,
            "ci_lower": None,
            "ci_upper": None,
            "n_group1": 0,
            "n_group2": 0,
            "status": "insufficient_groups"
        }

    # Identify groups (assuming 'nostalgia' and 'control')
    group1_name = groups[0]
    group2_name = groups[1]

    group1_data = valid_df[valid_df[group_col] == group1_name][metric].values
    group2_data = valid_df[valid_df[group_col] == group2_name][metric].values

    # Check for zero variance
    if np.var(group1_data) == 0 or np.var(group2_data) == 0:
        log_warning(f"Zero variance detected in one or both groups for {metric}")
        return {
            "metric": metric,
            "cohens_d": None,
            "ci_lower": None,
            "ci_upper": None,
            "n_group1": len(group1_data),
            "n_group2": len(group2_data),
            "status": "zero_variance"
        }

    # Calculate Cohen's d and CI
    cohens_d, ci_lower, ci_upper = calculate_cohen_d(group1_data, group2_data)

    return {
        "metric": metric,
        "group1": group1_name,
        "group2": group2_name,
        "n_group1": len(group1_data),
        "n_group2": len(group2_data),
        "cohens_d": round(cohens_d, 4),
        "ci_lower": round(ci_lower, 4),
        "ci_upper": round(ci_upper, 4),
        "ci_confidence": 0.95,
        "status": "success"
    }

def run_effect_size_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run effect size analysis for all primary metrics.

    Args:
        df: Cleaned dataframe

    Returns:
        Dictionary containing all effect size results
    """
    metrics = ["perseverative_errors", "categories_completed"]
    results = {}

    for metric in metrics:
        log_info(f"Calculating effect size for {metric}")
        results[metric] = calculate_effect_sizes(df, metric)

    return results

def save_results(results: Dict[str, Any], output_path: str = "data/results/effect_sizes.json") -> None:
    """Save effect size results to JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "timestamp": get_timestamp(),
        "task_id": "T020",
        "description": "Effect Size Calculation (Cohen's d with 95% CI)",
        "results": results
    }

    with open(path, 'w') as f:
        json.dump(output, f, indent=2)

    log_info(f"Effect size results saved to {output_path}")

def main():
    """Main entry point for Task T020."""
    logger.info("Starting Task T020: Effect Size Calculation")

    try:
        # Load cleaned dataset
        df = load_cleaned_dataset()
        log_info(f"Loaded dataset with {len(df)} records")

        # Run effect size analysis
        results = run_effect_size_analysis(df)

        # Save results
        save_results(results)

        log_info("Task T020 completed successfully")
        return results

    except FileNotFoundError as e:
        log_error(f"File not found: {e}")
        raise
    except Exception as e:
        log_error(f"Error during effect size calculation: {e}")
        raise

if __name__ == "__main__":
    main()
