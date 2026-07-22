"""
Metrics and analysis for the simulation pipeline.
Implements aggregation, confidence intervals, mixed-effects models, and sensitivity analysis.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.proportion import proportion_confint

# Import local utilities if needed, otherwise rely on standard libs
# Ensure paths are relative to the project root when imported via code/

logger = logging.getLogger(__name__)

# Constants
ALPHA_DEFAULT = 0.05
SENSITIVITY_ALPHA_LEVELS = [0.01, 0.05, 0.10]

def load_simulation_results(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load simulation results from CSV."""
    if filepath is None:
        filepath = "results/simulation_results.csv"
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Simulation results file not found at {filepath}")
    logger.info(f"Loading simulation results from {filepath}")
    return pd.read_csv(filepath)

def load_real_world_results(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load real world results from CSV."""
    if filepath is None:
        filepath = "results/real_world_results.csv"
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Real world results file not found at {filepath}")
    logger.info(f"Loading real world results from {filepath}")
    return pd.read_csv(filepath)

def calculate_confidence_interval(
    successes: int, total: int, alpha: float = 0.05
) -> Tuple[float, float]:
    """
    Calculate the Clopper-Pearson exact confidence interval for a binomial proportion.
    
    Args:
        successes: Number of successes (e.g., rejections of null)
        total: Total number of trials
        alpha: Significance level for the CI (e.g., 0.05 for 95% CI)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if total == 0:
        return 0.0, 0.0
    # statsmodels or scipy.stats.beta can be used. 
    # Using scipy.stats.beta for Clopper-Pearson
    lower = stats.beta.ppf(alpha / 2, successes, total - successes + 1) if successes > 0 else 0.0
    upper = stats.beta.ppf(1 - alpha / 2, successes + 1, total - successes) if successes < total else 1.0
    return lower, upper

def calculate_aggregate_metrics(
    results_df: pd.DataFrame, alpha: float = ALPHA_DEFAULT
) -> pd.DataFrame:
    """
    Calculate aggregate metrics (Type I error, Power) per configuration.
    
    Args:
        results_df: DataFrame with columns including 'p_value', 'ground_truth', 
                    'scaling_method', 'test_type', 'config_id'.
        alpha: Significance threshold.
                    
    Returns:
        DataFrame with aggregated metrics.
    """
    if results_df.empty:
        logger.warning("Input DataFrame is empty.")
        return pd.DataFrame()

    # Ensure numeric types
    results_df['p_value'] = pd.to_numeric(results_df['p_value'], errors='coerce')
    
    # Group by configuration
    groups = results_df.groupby(['config_id', 'scaling_method', 'test_type'])
    
    records = []
    for (config_id, scaling_method, test_type), group in groups:
        total = len(group)
        if total == 0:
            continue
            
        # Type I Error: Rejection rate when ground_truth is 'null'
        null_mask = group['ground_truth'] == 'null'
        null_count = null_mask.sum()
        null_rejections = (group.loc[null_mask, 'p_value'] < alpha).sum()
        type1_error = null_rejections / null_count if null_count > 0 else 0.0
        
        # Power: Rejection rate when ground_truth is 'alternative'
        alt_mask = group['ground_truth'] == 'alternative'
        alt_count = alt_mask.sum()
        alt_rejections = (group.loc[alt_mask, 'p_value'] < alpha).sum()
        power = alt_rejections / alt_count if alt_count > 0 else 0.0
        
        # Confidence Intervals
        ci_low_type1, ci_high_type1 = calculate_confidence_interval(null_rejections, null_count)
        ci_low_power, ci_high_power = calculate_confidence_interval(alt_rejections, alt_count)
        
        records.append({
            'config_id': config_id,
            'scaling_method': scaling_method,
            'test_type': test_type,
            'error_rate': type1_error,
            'power': power,
            'ci_lower': ci_low_type1,
            'ci_upper': ci_high_type1,
            'total_null': null_count,
            'total_alt': alt_count
        })
        
    return pd.DataFrame(records)

def fit_mixed_effects_model(
    df: pd.DataFrame, 
    response_col: str = 'error_rate',
    random_effect: str = 'config_id'
) -> Any:
    """
    Fit a linear mixed-effects model.
    
    Args:
        df: DataFrame containing the metrics.
        response_col: Name of the response variable.
        random_effect: Name of the grouping variable for random effects.
        
    Returns:
        statsmodels MixedLMResults object.
    """
    # Prepare formula
    # response ~ scaling_method + (1 | random_effect)
    formula = f"{response_col} ~ C(scaling_method)"
    if random_effect:
        formula += f" + (1 | {random_effect})"
        
    try:
        model = smf.mixedlm(formula, df, groups=df[random_effect])
        result = model.fit()
        logger.info("Mixed effects model fitted successfully.")
        return result
    except Exception as e:
        logger.error(f"Failed to fit mixed effects model: {e}")
        return None

def generate_comparison_report(
    synthetic_df: pd.DataFrame, 
    real_df: pd.DataFrame, 
    output_path: str = "results/comparison_report.md"
) -> None:
    """
    Generate a markdown comparison report between synthetic and real-world results.
    """
    # Calculate metrics
    # Assume synthetic_df and real_df have 'error_rate' and 'power' columns
    # Group by test_type and scaling_method to align
    
    report_lines = ["# Comparison Report: Synthetic vs Real-World Results\n\n"]
    report_lines.append("## Error Rate Comparison\n")
    report_lines.append("| Metric | Synthetic Value | Real Value | Mean Abs Diff | Correlation |\n")
    report_lines.append("| --- | --- | --- | --- | --- |\n")
    
    if synthetic_df.empty or real_df.empty:
        report_lines.append("| Note | Data missing for comparison | | | |\n")
    else:
        # Merge on common keys if possible, or just aggregate
        # For simplicity, compare global averages if grouping is complex
        syn_mean = synthetic_df['error_rate'].mean()
        real_mean = real_df['error_rate'].mean()
        mad = abs(syn_mean - real_mean)
        
        # Correlation
        if len(synthetic_df) > 1 and len(real_df) > 1:
            # Align rows? Assuming they are ordered similarly or just aggregate
            # A robust way is to merge on keys if they exist
            merged = pd.merge(synthetic_df, real_df, on=['scaling_method', 'test_type'], suffixes=('_syn', '_real'))
            if not merged.empty and len(merged) > 1:
                corr = merged['error_rate_syn'].corr(merged['error_rate_real'])
            else:
                corr = np.nan
        else:
            corr = np.nan
            
        report_lines.append(f"| Error Rate | {syn_mean:.4f} | {real_mean:.4f} | {mad:.4f} | {corr:.4f} |\n")
        
    report_lines.append("\n## Power Comparison\n")
    report_lines.append("| Metric | Synthetic Value | Real Value | Mean Abs Diff | Correlation |\n")
    report_lines.append("| --- | --- | --- | --- | --- |\n")
    
    if not synthetic_df.empty and not real_df.empty:
        syn_mean = synthetic_df['power'].mean()
        real_mean = real_df['power'].mean()
        mad = abs(syn_mean - real_mean)
        
        if len(synthetic_df) > 1 and len(real_df) > 1:
            merged = pd.merge(synthetic_df, real_df, on=['scaling_method', 'test_type'], suffixes=('_syn', '_real'))
            if not merged.empty and len(merged) > 1:
                corr = merged['power_syn'].corr(merged['power_real'])
            else:
                corr = np.nan
        else:
            corr = np.nan
            
        report_lines.append(f"| Power | {syn_mean:.4f} | {real_mean:.4f} | {mad:.4f} | {corr:.4f} |\n")
    
    with open(output_path, 'w') as f:
        f.writelines(report_lines)
    logger.info(f"Comparison report written to {output_path}")

def run_full_analysis_pipeline(
    results_df: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    Run the full analysis pipeline on simulation results.
    Accepts optional DataFrame or loads from default path.
    """
    if results_df is None:
        results_df = load_simulation_results()
        
    if results_df is None or results_df.empty:
        logger.error("No data available for analysis.")
        return {}

    # Calculate aggregate metrics
    aggregate_df = calculate_aggregate_metrics(results_df)
    
    # Save aggregate metrics
    output_path = "results/aggregate_metrics.csv"
    aggregate_df.to_csv(output_path, index=False)
    logger.info(f"Aggregate metrics saved to {output_path}")
    
    # Fit mixed effects model
    model = fit_mixed_effects_model(aggregate_df)
    
    return {
        'aggregate_metrics': aggregate_df,
        'mixed_effects_model': model
    }

def run_sensitivity_analysis(
    results_df: Optional[pd.DataFrame] = None,
    alpha_levels: Optional[List[float]] = None,
    output_path: str = "results/sensitivity_analysis.csv"
) -> pd.DataFrame:
    """
    Run sensitivity analysis for different alpha thresholds.
    Re-calculates Type I error rates and power for each alpha level.
    
    Args:
        results_df: DataFrame with simulation results. If None, loads from default.
        alpha_levels: List of alpha levels to test. Defaults to [0.01, 0.05, 0.10].
        output_path: Path to save the results CSV.
        
    Returns:
        DataFrame containing error rates and power for each alpha level and scaling method.
    """
    if alpha_levels is None:
        alpha_levels = SENSITIVITY_ALPHA_LEVELS
        
    if results_df is None:
        results_df = load_simulation_results()
        
    if results_df is None or results_df.empty:
        logger.error("No data available for sensitivity analysis.")
        return pd.DataFrame()

    logger.info(f"Running sensitivity analysis for alpha levels: {alpha_levels}")
    
    records = []
    
    # Ensure numeric
    results_df['p_value'] = pd.to_numeric(results_df['p_value'], errors='coerce')
    
    # Group by config, scaling, test
    groups = results_df.groupby(['config_id', 'scaling_method', 'test_type'])
    
    for alpha in alpha_levels:
        logger.info(f"Processing alpha = {alpha}")
        
        for (config_id, scaling_method, test_type), group in groups:
            total = len(group)
            if total == 0:
                continue
            
            # Type I Error
            null_mask = group['ground_truth'] == 'null'
            null_count = null_mask.sum()
            if null_count > 0:
                null_rejections = (group.loc[null_mask, 'p_value'] < alpha).sum()
                type1_error = null_rejections / null_count
                ci_low, ci_high = calculate_confidence_interval(null_rejections, null_count)
            else:
                type1_error = 0.0
                ci_low, ci_high = 0.0, 0.0
            
            # Power
            alt_mask = group['ground_truth'] == 'alternative'
            alt_count = alt_mask.sum()
            if alt_count > 0:
                alt_rejections = (group.loc[alt_mask, 'p_value'] < alpha).sum()
                power = alt_rejections / alt_count
                ci_low_p, ci_high_p = calculate_confidence_interval(alt_rejections, alt_count)
            else:
                power = 0.0
                ci_low_p, ci_high_p = 0.0, 0.0
            
            records.append({
                'alpha_level': alpha,
                'config_id': config_id,
                'scaling_method': scaling_method,
                'test_type': test_type,
                'error_rate': type1_error,
                'ci_lower': ci_low,
                'ci_upper': ci_high,
                'power': power,
                'power_ci_lower': ci_low_p,
                'power_ci_upper': ci_high_p,
                'total_null': null_count,
                'total_alt': alt_count
            })
    
    df_result = pd.DataFrame(records)
    df_result.to_csv(output_path, index=False)
    logger.info(f"Sensitivity analysis results saved to {output_path}")
    
    return df_result
