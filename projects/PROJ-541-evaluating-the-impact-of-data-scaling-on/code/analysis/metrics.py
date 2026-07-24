"""
Aggregation, metrics, and analysis functions.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats

# Import from local modules as per project structure
# Assuming these are available in the codebase as per the API surface
# If not, they should be imported from the correct relative paths
try:
    from analysis.tests import TestResult
except ImportError:
    # Fallback if running as main script or different import context
    TestResult = Any  # type: ignore

logger = logging.getLogger(__name__)

def load_simulation_results(filepath: str = "results/simulation_results.csv") -> pd.DataFrame:
    """Load simulation results from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Simulation results file not found: {filepath}")
    return pd.read_csv(filepath)

def load_real_world_results(filepath: str = "results/real_world_results.csv") -> pd.DataFrame:
    """Load real world results from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Real world results file not found: {filepath}")
    return pd.read_csv(filepath)

def calculate_aggregate_metrics(
    df: pd.DataFrame,
    alpha: float = 0.05
) -> pd.DataFrame:
    """
    Calculate aggregate metrics (Type I error, Power) for each config/scaling/test.

    Formula:
    Type I error = count(p < alpha) / total_iterations (for null hypothesis)
    Power = count(p < alpha) / total_iterations (for alternative hypothesis)

    Args:
        df: DataFrame with columns: config_id, scaling_method, test_type, p_value, ground_truth
        alpha: Significance threshold

    Returns:
        DataFrame with metrics per group
    """
    if df.empty:
        return pd.DataFrame()

    # Ensure p_value is numeric
    df = df.copy()
    df['p_value'] = pd.to_numeric(df['p_value'], errors='coerce')

    # Group by config, scaling, test
    groups = df.groupby(['config_id', 'scaling_method', 'test_type', 'ground_truth'])

    results = []
    for (config_id, scaling_method, test_type, ground_truth), group in groups:
        total = len(group)
        if total == 0:
            continue

        significant = (group['p_value'] < alpha).sum()
        error_rate = significant / total if total > 0 else 0.0

        # Determine if this is null or alternative
        is_null = ground_truth == 'null'

        results.append({
            'config_id': config_id,
            'scaling_method': scaling_method,
            'test_type': test_type,
            'ground_truth': ground_truth,
            'total_iterations': total,
            'significant_count': int(significant),
            'error_rate': error_rate,
            'is_null': is_null
        })

    result_df = pd.DataFrame(results)

    # Pivot to get error_rate and power separately
    # For null: error_rate is Type I error
    # For alternative: error_rate is Power
    if result_df.empty:
        return result_df

    # Calculate CI using Clopper-Pearson
    def clopper_pearson_ci(successes, n, alpha_conf=0.05):
        if n == 0:
            return 0.0, 0.0
        if successes == 0:
            lower = 0.0
            upper = 1 - (alpha_conf / 2) ** (1 / n)
        elif successes == n:
            lower = (alpha_conf / 2) ** (1 / n)
            upper = 1.0
        else:
            lower = stats.beta.ppf(alpha_conf / 2, successes, n - successes + 1)
            upper = stats.beta.ppf(1 - alpha_conf / 2, successes + 1, n - successes)
        return lower, upper

    ci_results = []
    for _, row in result_df.iterrows():
        lower, upper = clopper_pearson_ci(row['significant_count'], row['total_iterations'])
        ci_results.append({
            'config_id': row['config_id'],
            'scaling_method': row['scaling_method'],
            'test_type': row['test_type'],
            'ground_truth': row['ground_truth'],
            'error_rate': row['error_rate'],
            'ci_lower': lower,
            'ci_upper': upper,
            'total_iterations': row['total_iterations'],
            'significant_count': row['significant_count']
        })

    return pd.DataFrame(ci_results)

def calculate_confidence_interval(
    successes: int,
    n: int,
    alpha_conf: float = 0.05
) -> Tuple[float, float]:
    """
    Calculate Clopper-Pearson exact confidence interval.

    Args:
        successes: Number of successes
        n: Total trials
        alpha_conf: Confidence level (e.g., 0.05 for 95% CI)

    Returns:
        (lower, upper) tuple
    """
    if n == 0:
        return 0.0, 0.0
    if successes == 0:
        lower = 0.0
        upper = 1 - (alpha_conf / 2) ** (1 / n)
    elif successes == n:
        lower = (alpha_conf / 2) ** (1 / n)
        upper = 1.0
    else:
        lower = stats.beta.ppf(alpha_conf / 2, successes, n - successes + 1)
        upper = stats.beta.ppf(1 - alpha_conf / 2, successes + 1, n - successes)
    return lower, upper

def fit_mixed_effects_model(
    df: pd.DataFrame,
    model_type: str = "synthetic"
) -> Any:
    """
    Fit a mixed-effects model to analyze the impact of scaling methods.

    For synthetic data: model ~ scaling_method + (1 | config_id)
    For real-world data: model ~ scaling_method + (1 | dataset_id)

    Args:
        df: DataFrame with metrics
        model_type: 'synthetic' or 'real_world'

    Returns:
        Model summary object
    """
    try:
        import statsmodels.formula.api as smf
    except ImportError:
        logger.warning("statsmodels not available. Skipping mixed-effects model.")
        return None

    # Prepare data
    df_clean = df.dropna(subset=['error_rate', 'scaling_method'])

    if model_type == "synthetic":
        if 'config_id' not in df_clean.columns:
            logger.warning("config_id not found in data for synthetic model.")
            return None
        formula = "error_rate ~ scaling_method + (1 | config_id)"
    else:
        if 'dataset_id' not in df_clean.columns:
            logger.warning("dataset_id not found in data for real-world model.")
            return None
        formula = "error_rate ~ scaling_method + (1 | dataset_id)"

    try:
        model = smf.mixedlm(formula, df_clean, groups=df_clean['config_id'] if model_type == "synthetic" else df_clean['dataset_id'])
        result = model.fit()
        return result
    except Exception as e:
        logger.error(f"Failed to fit mixed-effects model: {e}")
        return None

def generate_comparison_report(
    synthetic_df: pd.DataFrame,
    real_df: pd.DataFrame,
    output_path: str = "results/comparison_report.md"
) -> None:
    """
    Generate a markdown comparison report between synthetic and real-world results.

    Args:
        synthetic_df: Synthetic results DataFrame
        real_df: Real-world results DataFrame
        output_path: Path to save the report
    """
    # Aggregate both
    synth_agg = calculate_aggregate_metrics(synthetic_df)
    real_agg = calculate_aggregate_metrics(real_df)

    # Compute metrics
    # Mean Absolute Difference
    if not synth_agg.empty and not real_agg.empty:
        # Merge on common keys if possible, or just compare overall means
        mean_synth = synth_agg['error_rate'].mean()
        mean_real = real_agg['error_rate'].mean()
        mad = abs(mean_synth - mean_real)

        # Correlation (if we can align them)
        # For simplicity, we compare overall distributions if not aligned
        corr = np.corrcoef(synth_agg['error_rate'].dropna(), real_agg['error_rate'].dropna())[0, 1] if len(synth_agg) > 1 and len(real_agg) > 1 else np.nan
    else:
        mad = np.nan
        corr = np.nan

    report = f"""# Comparison Report: Synthetic vs Real-World Results

## Summary Metrics

| Metric | Synthetic Value | Real Value | Mean Absolute Difference | Correlation Coefficient |
|--------|-----------------|------------|--------------------------|-------------------------|
| Error Rate | {mean_synth if not synth_agg.empty else 'N/A':.4f} | {mean_real if not real_agg.empty else 'N/A':.4f} | {mad:.4f} | {corr:.4f} |

## Detailed Breakdown

### Synthetic Results
{synth_agg.to_markdown() if not synth_agg.empty else "No synthetic data available."}

### Real-World Results
{real_agg.to_markdown() if not real_agg.empty else "No real-world data available."}
"""

    with open(output_path, 'w') as f:
        f.write(report)
    logger.info(f"Comparison report saved to {output_path}")

def run_sensitivity_analysis(
    input_path: str = "results/simulation_results.csv",
    output_path: str = "results/sensitivity_analysis.csv",
    alpha_levels: Optional[List[float]] = None
) -> pd.DataFrame:
    """
    Run sensitivity analysis for a range of alpha thresholds.

    Reads raw simulation results and recalculates error rates and power
    for each specified alpha level.

    Args:
        input_path: Path to simulation_results.csv
        output_path: Path to save sensitivity_analysis.csv
        alpha_levels: List of alpha thresholds to test. Defaults to [0.01, 0.05, 0.10]

    Returns:
        DataFrame with sensitivity analysis results
    """
    if alpha_levels is None:
        alpha_levels = [0.01, 0.05, 0.10]

    logger.info(f"Running sensitivity analysis with alpha levels: {alpha_levels}")

    # Load data
    df = load_simulation_results(input_path)
    if df.empty:
        logger.warning("Input data is empty. Returning empty result.")
        return pd.DataFrame()

    # Ensure p_value is numeric
    df['p_value'] = pd.to_numeric(df['p_value'], errors='coerce')

    results = []

    for alpha in alpha_levels:
        # Calculate aggregate metrics for this alpha
        agg_df = calculate_aggregate_metrics(df, alpha=alpha)
        agg_df['alpha_level'] = alpha
        results.append(agg_df)

    if not results:
        return pd.DataFrame()

    combined_df = pd.concat(results, ignore_index=True)

    # Save to CSV
    combined_df.to_csv(output_path, index=False)
    logger.info(f"Sensitivity analysis saved to {output_path}")

    return combined_df

def run_full_analysis_pipeline(
    df: Optional[pd.DataFrame] = None,
    input_path: str = "results/simulation_results.csv",
    output_path: str = "results/aggregate_metrics.csv"
) -> pd.DataFrame:
    """
    Run the full analysis pipeline: load data, calculate aggregate metrics, and save results.

    This function is tolerant of being called with or without a DataFrame argument.

    Args:
        df: Optional DataFrame. If provided, used directly.
        input_path: Path to input CSV if df is not provided.
        output_path: Path to save results.

    Returns:
        DataFrame with aggregate metrics
    """
    # Handle both call signatures
    if df is None:
        # Called as run_full_analysis_pipeline() -> load from path
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        df = load_simulation_results(input_path)
    else:
        # Called as run_full_analysis_pipeline(df) -> use provided df
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Expected a pandas DataFrame")

    if df.empty:
        logger.warning("Input data is empty.")
        return pd.DataFrame()

    # Calculate metrics
    metrics_df = calculate_aggregate_metrics(df)

    # Save if path provided
    if output_path:
        metrics_df.to_csv(output_path, index=False)
        logger.info(f"Aggregate metrics saved to {output_path}")

    return metrics_df