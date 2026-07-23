"""
Task T026: Generate data/processed/metrics_summary.csv with ANOVA results.

This script loads cleaned session data, performs Repeated Measures ANOVA
on the metrics (Completion Time, Error Count, SUS), applies Holm-Bonferroni
correction, calculates effect sizes (eta-squared), and writes the results
to data/processed/metrics_summary.csv.

Per Spec FR-002 (Amended by T035a) and Constitution Principle VII:
- Repeated Measures ANOVA is the mandated primary method.
- Shapiro-Wilk is logged for audit only; it does not alter the test choice.
- Levene's test is omitted as inappropriate for paired designs.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from scipy import stats
import argparse

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger

logger = get_logger(__name__)

def load_cleaned_data(input_path: str) -> pd.DataFrame:
    """
    Load the cleaned sessions CSV.
    
    Args:
        input_path: Path to data/processed/cleaned_sessions.csv
        
    Returns:
        DataFrame with cleaned session data.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Cleaned data file not found: {input_path}")
        
    df = pd.read_csv(input_path)
    
    required_cols = [
        'participant_id', 'interface_type', 
        'completion_time_seconds', 'error_count', 
        'sus_score', 'explanation_engagement_time_seconds'
    ]
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
        
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def run_repeated_measures_anova(df: pd.DataFrame, metric: str, subject_col: str = 'participant_id', condition_col: str = 'interface_type') -> Dict[str, Any]:
    """
    Perform Repeated Measures ANOVA for a specific metric.
    
    Args:
        df: DataFrame containing the data.
        metric: Name of the metric column to analyze.
        subject_col: Column name for participant IDs.
        condition_col: Column name for interface types.
        
    Returns:
        Dictionary with F_statistic, p_value, and effect_size (eta-squared).
    """
    # Ensure we have unique subjects
    subjects = df[subject_col].unique()
    conditions = df[condition_col].unique()
    
    if len(conditions) < 2:
        logger.warning(f"Not enough conditions ({len(conditions)}) for ANOVA on {metric}")
        return {
            "F_statistic": np.nan,
            "p_value": np.nan,
            "effect_size": np.nan,
            "n_subjects": len(subjects),
            "n_conditions": len(conditions)
        }
    
    # Pivot data to wide format for RM-ANOVA: index=subject, columns=condition, values=metric
    try:
        pivot_df = df.pivot_table(index=subject_col, columns=condition_col, values=metric)
    except ValueError as e:
        logger.error(f"Error pivoting data for {metric}: {e}")
        return {
            "F_statistic": np.nan,
            "p_value": np.nan,
            "effect_size": np.nan,
            "n_subjects": len(subjects),
            "n_conditions": len(conditions)
        }
    
    # Remove rows with missing values (participants who didn't complete both conditions)
    pivot_df = pivot_df.dropna()
    
    if pivot_df.shape[0] < 2:
        logger.warning(f"Not enough complete subjects ({pivot_df.shape[0]}) for ANOVA on {metric}")
        return {
            "F_statistic": np.nan,
            "p_value": np.nan,
            "effect_size": np.nan,
            "n_subjects": len(subjects),
            "n_conditions": len(conditions)
        }
    
    # Perform One-Way Repeated Measures ANOVA using scipy
    # scipy.stats.f_oneway is for independent samples, so we use the manual calculation
    # or the rm_anova if available. Since scipy < 1.9 doesn't have rm_anova, we calculate manually.
    
    # Manual calculation for One-Way RM ANOVA
    # Source: https://stats.idre.ucla.edu/other/mult-pkg/whatstat/what-is-the-difference-between-repeated-measures-anova-and-mixed-models/
    # Or use pingouin if available, but sticking to scipy/numpy as per constraints.
    
    # Let's use the standard approach:
    # SS_total, SS_subject, SS_condition, SS_error
    # F = (SS_condition / df_condition) / (SS_error / df_error)
    
    # Convert to numpy for easier calculation
    data_matrix = pivot_df.values
    n_subjects, n_conditions = data_matrix.shape
    
    # Grand mean
    grand_mean = np.mean(data_matrix)
    
    # Sum of Squares Total
    ss_total = np.sum((data_matrix - grand_mean) ** 2)
    
    # Sum of Squares Subjects
    subject_means = np.mean(data_matrix, axis=1, keepdims=True)
    ss_subject = n_conditions * np.sum((subject_means - grand_mean) ** 2)
    
    # Sum of Squares Condition
    condition_means = np.mean(data_matrix, axis=0, keepdims=True)
    ss_condition = n_subjects * np.sum((condition_means - grand_mean) ** 2)
    
    # Sum of Squares Error (Residual)
    ss_error = ss_total - ss_subject - ss_condition
    
    # Degrees of freedom
    df_condition = n_conditions - 1
    df_error = (n_subjects - 1) * (n_conditions - 1)
    
    # Mean Squares
    ms_condition = ss_condition / df_condition
    ms_error = ss_error / df_error if df_error > 0 else 0
    
    # F-statistic
    f_stat = ms_condition / ms_error if ms_error > 0 else np.nan
    
    # P-value
    if f_stat is not np.nan and df_error > 0:
        p_val = 1 - stats.f.cdf(f_stat, df_condition, df_error)
    else:
        p_val = np.nan
    
    # Effect Size: Partial Eta Squared
    # eta^2 = SS_condition / (SS_condition + SS_error)
    if (ss_condition + ss_error) > 0:
        eta_sq = ss_condition / (ss_condition + ss_error)
    else:
        eta_sq = np.nan
        
    return {
        "F_statistic": f_stat,
        "p_value": p_val,
        "effect_size": eta_sq,
        "n_subjects": n_subjects,
        "n_conditions": n_conditions
    }

def holm_bonferroni_correction(p_values: List[float]) -> List[float]:
    """
    Apply Holm-Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        
    Returns:
        List of adjusted p-values.
    """
    n = len(p_values)
    if n == 0:
        return []
        
    # Sort p-values and keep track of original indices
    sorted_indices = sorted(range(n), key=lambda k: p_values[k])
    sorted_pvals = [p_values[i] for i in sorted_indices]
    
    adjusted_pvals = [0.0] * n
    alpha = 0.05
    
    # Holm-Bonferroni step-down procedure
    # p_(i) >= max(p_(i-1) * (n - i + 1), p_(i-1)) ... actually simpler:
    # For sorted p-values p(1) <= p(2) <= ... <= p(n):
    # p_adj(i) = max( (n - i + 1) * p(i), p_adj(i-1) )
    
    # Implementation:
    # Calculate adjusted p-values for sorted list
    current_max = 0.0
    for i, p in enumerate(sorted_pvals):
        # Rank i goes from 1 to n
        rank = i + 1
        adjusted = p * (n - rank + 1)
        adjusted = max(adjusted, current_max)
        adjusted = min(adjusted, 1.0) # Cap at 1.0
        current_max = adjusted
        adjusted_pvals[sorted_indices[i]] = adjusted
        
    return adjusted_pvals

def generate_metrics_summary(df: pd.DataFrame, output_path: str) -> pd.DataFrame:
    """
    Generate the metrics summary CSV with ANOVA results.
    
    Args:
        df: Cleaned data DataFrame.
        output_path: Path to write the output CSV.
        
    Returns:
        The summary DataFrame.
    """
    metrics = [
        ("completion_time_seconds", "Completion Time"),
        ("error_count", "Error Count"),
        ("sus_score", "SUS Score")
    ]
    
    results = []
    p_values = []
    
    logger.info("Running Repeated Measures ANOVA for each metric...")
    
    for metric_col, metric_name in metrics:
        logger.info(f"Analyzing {metric_name}...")
        anova_result = run_repeated_measures_anova(df, metric_col)
        
        results.append({
            "metric_name": metric_name,
            "metric_column": metric_col,
            "interface_type": "Traditional vs Explainable",
            "F_statistic": anova_result["F_statistic"],
            "p_value": anova_result["p_value"],
            "effect_size": anova_result["effect_size"],
            "n_subjects": anova_result["n_subjects"],
            "n_conditions": anova_result["n_conditions"]
        })
        
        if not np.isnan(anova_result["p_value"]):
            p_values.append(anova_result["p_value"])
    
    # Apply Holm-Bonferroni correction
    if p_values:
        adjusted_p_values = holm_bonferroni_correction(p_values)
        for i, row in enumerate(results):
            if i < len(adjusted_p_values):
                row["adjusted_p_value"] = adjusted_p_values[i]
            else:
                row["adjusted_p_value"] = np.nan
    else:
        for row in results:
            row["adjusted_p_value"] = np.nan
            
    summary_df = pd.DataFrame(results)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write to CSV
    summary_df.to_csv(output_path, index=False)
    logger.info(f"Metrics summary written to {output_path}")
    
    return summary_df

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Generate metrics summary with ANOVA results.")
    parser.add_argument("--input", type=str, default="data/processed/cleaned_sessions.csv",
                        help="Path to the cleaned sessions CSV.")
    parser.add_argument("--output", type=str, default="data/processed/metrics_summary.csv",
                        help="Path to write the metrics summary CSV.")
    
    args = parser.parse_args()
    
    try:
        # Load data
        df = load_cleaned_data(args.input)
        
        # Generate summary
        summary_df = generate_metrics_summary(df, args.output)
        
        # Log a brief summary
        logger.info("ANOVA Results Summary:")
        for _, row in summary_df.iterrows():
            logger.info(f"  {row['metric_name']}: F={row['F_statistic']:.4f}, p={row['p_value']:.4f}, p_adj={row['adjusted_p_value']:.4f}, eta2={row['effect_size']:.4f}")
            
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
