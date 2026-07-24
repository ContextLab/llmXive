"""
Module to generate the metrics_summary.csv file containing ANOVA results.

This script implements the Repeated Measures ANOVA, Holm-Bonferroni correction,
and effect size calculation as defined in the project specification.

Per Spec FR-002 (Amended by T035a) and Constitution Principle VII,
Repeated Measures ANOVA is used for all metrics.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from scipy import stats

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger

logger = get_logger(__name__)

def load_cleaned_data(input_path: str) -> pd.DataFrame:
    """
    Load the cleaned session data from CSV.
    
    Args:
        input_path: Path to the cleaned_sessions.csv file.
        
    Returns:
        DataFrame containing the cleaned session data.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Cleaned data file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    required_columns = [
        'participant_id', 'interface_type', 'completion_time_seconds',
        'error_count', 'sus_score', 'explanation_engagement_time_seconds'
    ]
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Filter out explanation_engagement_time from ANOVA input as per spec
    # (It is reported descriptively only, not in inferential testing)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def run_repeated_measures_anova(df: pd.DataFrame, metric: str) -> Dict[str, Any]:
    """
    Run Repeated Measures ANOVA for a specific metric.
    
    Args:
        df: DataFrame with session data.
        metric: The metric column name to analyze.
        
    Returns:
        Dictionary containing F-statistic, p-value, and effect size.
    """
    # Ensure data is sorted for consistent pairing
    df = df.sort_values(['participant_id', 'interface_type'])
    
    # Pivot to get wide format: rows=participants, cols=interfaces
    try:
        pivot_df = df.pivot(index='participant_id', columns='interface_type', values=metric)
    except KeyError as e:
        logger.error(f"Pivot failed for metric {metric}: {e}")
        return None
    
    # Ensure we have both conditions
    if 'traditional' not in pivot_df.columns or 'explainable' not in pivot_df.columns:
        logger.warning(f"Missing one of the interface types for metric {metric}")
        return None
    
    # Extract paired samples
    traditional = pivot_df['traditional'].dropna()
    explainable = pivot_df['explainable'].dropna()
    
    # Align indices to ensure we are comparing the same participants
    common_idx = traditional.index.intersection(explainable.index)
    if len(common_idx) < 2:
        logger.warning(f"Insufficient paired data for metric {metric} (n={len(common_idx)})")
        return None
    
    x1 = traditional.loc[common_idx]
    x2 = explainable.loc[common_idx]
    
    # Repeated Measures ANOVA using F-test on paired differences
    # scipy.stats.f_oneway is for independent samples, so we use t-test for paired
    # and convert to F = t^2 for 2 conditions (equivalent to RM-ANOVA F)
    # However, for strict RM-ANOVA implementation with >2 conditions, we'd use statsmodels.
    # For 2 conditions (Traditional vs Explainable), Paired T-test F-statistic is appropriate.
    t_stat, p_val = stats.ttest_rel(x1, x2)
    f_stat = t_stat ** 2
    
    # Calculate Effect Size (Eta-squared / Partial Eta-squared for 2 groups)
    # eta^2 = t^2 / (t^2 + df) where df = n - 1
    n = len(common_idx)
    df_error = n - 1
    eta_squared = f_stat / (f_stat + df_error)
    
    return {
        'F_statistic': f_stat,
        'p_value': p_val,
        'effect_size': eta_squared,
        'n_participants': n
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
    
    # Sort p-values with their original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    adjusted_p = np.zeros(n)
    for i, p in enumerate(sorted_p):
        # Holm step-down: p * (n - i)
        adjusted = p * (n - i)
        # Ensure it doesn't exceed 1
        adjusted = min(adjusted, 1.0)
        # Ensure monotonicity (cumulative max from the end)
        adjusted_p[sorted_indices[i]] = adjusted
    
    # Enforce monotonicity: adjusted p[i] <= adjusted p[i+1]
    # We need to ensure that if we sorted, the corrected values don't decrease
    # Actually, Holm-Bonferroni requires checking against previous max
    # Simplified approach: sort, adjust, then cummax from right to left? 
    # Standard Holm: p_(i) * (m - i + 1). Then ensure p_(i) >= p_(i-1)
    
    # Re-implementation for strict Holm-Bonferroni
    sorted_p = sorted(p_values)
    m = len(sorted_p)
    corrected = []
    for i, p in enumerate(sorted_p):
        val = p * (m - i)
        val = min(val, 1.0)
        corrected.append(val)
    
    # Ensure non-decreasing order (cumulative max)
    for i in range(1, len(corrected)):
        corrected[i] = max(corrected[i], corrected[i-1])
    
    # Map back to original order
    result = [0.0] * n
    for i, idx in enumerate(sorted_indices):
        result[idx] = corrected[i]
        
    return result

def generate_metrics_summary(df: pd.DataFrame, output_path: str) -> bool:
    """
    Generate the metrics_summary.csv file with ANOVA results.
    
    Args:
        df: Cleaned session data.
        output_path: Path to write the output CSV.
        
    Returns:
        True if successful, False otherwise.
    """
    metrics = ['completion_time_seconds', 'error_count', 'sus_score']
    results = []
    
    raw_p_values = []
    
    logger.info(f"Running ANOVA for metrics: {metrics}")
    
    for metric in metrics:
        logger.info(f"Analyzing {metric}...")
        result = run_repeated_measures_anova(df, metric)
        
        if result is None:
            logger.warning(f"Skipping {metric} due to insufficient data or error.")
            continue
        
        raw_p_values.append(result['p_value'])
        
        results.append({
            'metric_name': metric,
            'interface_type': 'Traditional vs Explainable',
            'F_statistic': result['F_statistic'],
            'p_value': result['p_value'],
            'effect_size': result['effect_size'],
            'n_participants': result['n_participants']
        })
    
    if not results:
        logger.error("No results generated. Check data availability.")
        return False
    
    # Apply Holm-Bonferroni correction
    adjusted_p_values = holm_bonferroni_correction(raw_p_values)
    
    # Update results with adjusted p-values
    for i, res in enumerate(results):
        res['adjusted_p_value'] = adjusted_p_values[i]
    
    # Create DataFrame and write to CSV
    summary_df = pd.DataFrame(results)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    summary_df.to_csv(output_path, index=False)
    logger.info(f"Metrics summary written to {output_path}")
    
    # Log primary test verification (T024a)
    primary_p = results[0]['p_value'] if results else 1.0
    verification_path = output_path.replace('metrics_summary.csv', 'primary_test_verification.txt')
    with open(verification_path, 'w') as f:
        f.write(f"Primary ANOVA P-value: {primary_p}\n")
        f.write(f"Threshold: 0.05\n")
        f.write(f"Result: {'Significant' if primary_p < 0.05 else 'Not Significant'}\n")
        f.write("Holm-Bonferroni correction applied for multiple comparisons.\n")
    
    return True

def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate metrics summary from cleaned data.')
    parser.add_argument('--input', type=str, default='data/processed/cleaned_sessions.csv',
                        help='Path to cleaned sessions CSV')
    parser.add_argument('--output', type=str, default='data/processed/metrics_summary.csv',
                        help='Path to output metrics summary CSV')
    
    args = parser.parse_args()
    
    try:
        logger.info(f"Starting metrics summary generation...")
        df = load_cleaned_data(args.input)
        success = generate_metrics_summary(df, args.output)
        
        if success:
            logger.info("Metrics summary generation completed successfully.")
            sys.exit(0)
        else:
            logger.error("Metrics summary generation failed.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error during metrics summary generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
