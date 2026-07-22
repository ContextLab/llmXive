"""
Module to generate metrics_summary.csv using Repeated Measures ANOVA and Holm-Bonferroni correction.
This module implements the statistical analysis engine mandated by Spec FR-002 (Amended by T035a).
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from scipy import stats

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.logger import get_logger

logger = get_logger(__name__)

def load_cleaned_data(input_path: str) -> pd.DataFrame:
    """
    Load the cleaned sessions CSV.
    Validates that required columns exist.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {input_path}")
    
    df = pd.read_csv(path)
    
    required_columns = [
        'participant_id', 
        'interface_type', 
        'completion_time_seconds', 
        'error_count', 
        'sus_score',
        'explanation_engagement_time_seconds'
    ]
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in cleaned data: {missing_cols}")
    
    # Filter out incomplete sessions just in case (should be done in T021a)
    if 'status' in df.columns:
        df = df[df['status'] == 'complete'].copy()
    
    logger.info(f"Loaded {len(df)} completed sessions from {input_path}")
    return df

def run_repeated_measures_anova(df: pd.DataFrame, metric_col: str) -> Dict[str, Any]:
    """
    Perform Repeated Measures ANOVA for a specific metric across interface types.
    Returns F-statistic, p-value, and effect size (eta-squared).
    """
    # Group by participant and interface
    # We expect a wide format for rm_anova or need to reshape
    # Reshape to wide: columns are interfaces, rows are participants
    pivot_df = df.pivot_table(index='participant_id', columns='interface_type', values=metric_col)
    
    # Drop participants with missing data in either condition
    pivot_df = pivot_df.dropna()
    
    if len(pivot_df) < 2:
        logger.warning(f"Not enough participants with complete data for {metric_col} to run ANOVA.")
        return {
            'metric_name': metric_col,
            'F_statistic': np.nan,
            'p_value': np.nan,
            'effect_size': np.nan,
            'n_participants': len(pivot_df)
        }
    
    # Extract arrays for each interface
    # Assuming columns are 'traditional' and 'explainable'
    cols = list(pivot_df.columns)
    if len(cols) != 2:
        logger.warning(f"Expected 2 interface types, found {len(cols)}. Skipping ANOVA.")
        return {
            'metric_name': metric_col,
            'F_statistic': np.nan,
            'p_value': np.nan,
            'effect_size': np.nan,
            'n_participants': len(pivot_df)
        }
    
    group1 = pivot_df[cols[0]].values
    group2 = pivot_df[cols[1]].values
    
    # Repeated measures ANOVA using scipy
    # Since scipy doesn't have a direct rm_anova function for 2 groups (equivalent to paired t-test squared),
    # we use f_oneway on the differences? No, that's not right.
    # For 2 conditions, RM ANOVA F = t^2 from paired t-test.
    # However, to be general and use the standard library as requested:
    # We can use pingouin if available, but sticking to scipy:
    # We perform a one-way repeated measures ANOVA manually or use f_oneway on the residuals?
    # Actually, for 2 groups, a paired t-test is the standard.
    # But the spec says ANOVA. F-statistic for paired t-test is t^2.
    
    # Let's use the standard approach for 2 groups: Paired T-Test, then square t to get F.
    # Or use stats.f_oneway if we treat it as independent (wrong) -> No.
    # Correct approach for 2 groups in RM:
    t_stat, p_val = stats.ttest_rel(group1, group2)
    f_stat = t_stat ** 2
    
    # Effect size: Eta-squared (partial eta squared for RM)
    # Eta^2 = SS_effect / (SS_effect + SS_error)
    # For paired t-test, eta^2 = t^2 / (t^2 + df)
    df_error = len(group1) - 1
    eta_squared = (t_stat ** 2) / (t_stat ** 2 + df_error)
    
    return {
        'metric_name': metric_col,
        'F_statistic': f_stat,
        'p_value': p_val,
        'effect_size': eta_squared,
        'n_participants': len(pivot_df)
    }

def holm_bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Apply Holm-Bonferroni correction to a list of p-values.
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values and keep track of original indices
    sorted_indices = sorted(range(n), key=lambda k: p_values[k])
    sorted_p = [p_values[i] for i in sorted_indices]
    
    corrected_p = []
    alpha = 0.05
    
    # Holm-Bonferroni step-down procedure
    # Compare p_(i) with alpha / (n - i + 1)
    # If p_(i) > alpha / (n - i + 1), stop and set all remaining to 1? 
    # Actually, the correction produces adjusted p-values.
    # Adjusted p_i = max( (n - j + 1) * p_(j) for j <= i )
    
    adj_p = [0.0] * n
    current_max = 0.0
    
    for i in range(n):
        # Calculate raw adjusted p-value for this rank
        raw_adj = sorted_p[i] * (n - i)
        if raw_adj > 1.0:
            raw_adj = 1.0
        if raw_adj > current_max:
            current_max = raw_adj
        else:
            raw_adj = current_max # Enforce monotonicity
        
        adj_p[sorted_indices[i]] = raw_adj
    
    return adj_p

def generate_metrics_summary(df: pd.DataFrame, output_path: str) -> None:
    """
    Main function to orchestrate ANOVA and write the summary CSV.
    """
    metrics = ['completion_time_seconds', 'error_count', 'sus_score']
    
    results = []
    p_values = []
    
    logger.info("Starting Repeated Measures ANOVA for all metrics...")
    
    for metric in metrics:
        logger.info(f"Running ANOVA for {metric}...")
        try:
            res = run_repeated_measures_anova(df, metric)
            results.append(res)
            if not np.isnan(res['p_value']):
                p_values.append(res['p_value'])
            logger.info(f"  F={res['F_statistic']:.4f}, p={res['p_value']:.4f}, eta2={res['effect_size']:.4f}")
        except Exception as e:
            logger.error(f"Error running ANOVA for {metric}: {e}")
            results.append({
                'metric_name': metric,
                'F_statistic': np.nan,
                'p_value': np.nan,
                'effect_size': np.nan,
                'n_participants': 0
            })
    
    # Apply Holm-Bonferroni correction
    if p_values:
        corrected_p = holm_bonferroni_correction(p_values)
        # Map corrected p-values back to results
        # Note: p_values list order matches results list order for valid p-values
        # We need to be careful with NaNs. Let's reconstruct.
        
        valid_indices = [i for i, r in enumerate(results) if not np.isnan(r['p_value'])]
        for idx, adj_p_val in zip(valid_indices, corrected_p):
            results[idx]['adjusted_p_value'] = adj_p_val
            logger.info(f"  Adjusted p-value for {results[idx]['metric_name']}: {adj_p_val:.4f}")
    else:
        for r in results:
            r['adjusted_p_value'] = np.nan
    
    # Create DataFrame and write to CSV
    # Ensure columns are in specific order
    output_cols = ['metric_name', 'interface_type', 'F_statistic', 'p_value', 'adjusted_p_value', 'effect_size']
    # interface_type is not per-row in this summary, it's the comparison. We can set it to 'Traditional vs Explainable'
    for r in results:
        r['interface_type'] = 'Traditional vs Explainable'
    
    # Fill missing adjusted_p_value with NaN if not set
    for r in results:
        if 'adjusted_p_value' not in r:
            r['adjusted_p_value'] = np.nan
    
    df_results = pd.DataFrame(results)
    df_results = df_results[output_cols]
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    df_results.to_csv(output_path, index=False)
    logger.info(f"Metrics summary written to {output_path}")

def main():
    """
    CLI entry point for generating metrics summary.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate metrics summary CSV with ANOVA results.")
    parser.add_argument("--input", type=str, default="data/processed/cleaned_sessions.csv",
                        help="Path to cleaned sessions CSV.")
    parser.add_argument("--output", type=str, default="data/processed/metrics_summary.csv",
                        help="Path to output metrics summary CSV.")
    
    args = parser.parse_args()
    
    try:
        df = load_cleaned_data(args.input)
        generate_metrics_summary(df, args.output)
        logger.info("Analysis completed successfully.")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
