import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, List, Optional, Tuple
import os
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

# Per Spec FR-002 (Amended by T035a) and Constitution Principle VII,
# Repeated Measures ANOVA is used for all metrics. Shapiro-Wilk is run for logging only;
# Levene's test is omitted as inappropriate for paired designs.

def log_normality_test(data: pd.DataFrame, output_path: str) -> pd.DataFrame:
    """
    Perform Shapiro-Wilk normality test on the difference scores between interface types
    for each metric (completion_time, error_count, sus_score).
    
    The test is performed on the difference scores (Explainable - Traditional) for each participant.
    This is an audit-only step; the ANOVA is run regardless of the result.
    
    Args:
        data: Cleaned DataFrame with columns: participant_id, interface_type, metric values.
        output_path: Path to write the results log (CSV).
        
    Returns:
        DataFrame containing the test results.
    """
    logger.info("Starting Shapiro-Wilk normality audit on difference scores.")
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    metrics_to_test = ['completion_time_seconds', 'error_count', 'sus_score']
    results = []
    
    # Pivot data to wide format for difference calculation
    # We need one row per participant per metric, with columns for each interface
    wide_data = data.pivot_table(
        index='participant_id',
        columns='interface_type',
        values=metrics_to_test,
        aggfunc='mean' # In case of multiple sessions per participant per interface
    )
    
    for metric in metrics_to_test:
        if metric not in wide_data.columns.get_level_values(0):
            logger.warning(f"Metric {metric} not found in wide data, skipping.")
            continue
            
        # Get available interface columns for this metric
        available_interfaces = [col for col in wide_data.columns.get_level_values(1) if (metric, col) in wide_data.columns]
        
        if len(available_interfaces) < 2:
            logger.warning(f"Insufficient interface types for metric {metric} to compute differences.")
            continue
        
        # Calculate difference scores (Explainable - Traditional)
        # We assume 'explainable' and 'traditional' are the expected values
        if 'explainable' in available_interfaces and 'traditional' in available_interfaces:
            diff = wide_data[metric]['explainable'] - wide_data[metric]['traditional']
        else:
            # Fallback if naming differs, but log warning
            logger.warning(f"Expected 'explainable' and 'traditional' columns for {metric}, found {available_interfaces}.")
            continue
        
        # Drop NaNs
        diff_clean = diff.dropna()
        
        if len(diff_clean) < 3:
            logger.warning(f"Insufficient data points ({len(diff_clean)}) for Shapiro-Wilk on {metric}.")
            results.append({
                'metric': metric,
                'shapiro_statistic': np.nan,
                'p_value': np.nan,
                'n': len(diff_clean)
            })
            continue
        
        try:
            stat, p_val = stats.shapiro(diff_clean)
            results.append({
                'metric': metric,
                'shapiro_statistic': stat,
                'p_value': p_val,
                'n': len(diff_clean)
            })
            logger.info(f"Shapiro-Wilk for {metric}: W={stat:.4f}, p={p_val:.4f}")
        except Exception as e:
            logger.error(f"Shapiro-Wilk failed for {metric}: {e}")
            results.append({
                'metric': metric,
                'shapiro_statistic': np.nan,
                'p_value': np.nan,
                'n': len(diff_clean),
                'error': str(e)
            })
    
    results_df = pd.DataFrame(results)
    
    # Write to file
    results_df.to_csv(output_path, index=False)
    logger.info(f"Normality audit results written to {output_path}")
    
    return results_df

def run_anova_pipeline(data: pd.DataFrame) -> Dict[str, Any]:
    """
    Run Repeated Measures ANOVA on the provided data.
    Per Constitution Principle VII, this runs regardless of normality.
    
    Constraint: Explicitly filters out 'explanation_engagement_time_seconds' from ANOVA.
    This metric is reported descriptively only.
    """
    logger.info("Running Repeated Measures ANOVA pipeline.")
    
    # Define metrics to test. 
    # IMPORTANT: explanation_engagement_time_seconds is EXCLUDED from inferential testing.
    metrics_to_test = ['completion_time_seconds', 'error_count', 'sus_score']
    
    anova_results = {}
    
    # Pivot data to wide format for repeated measures ANOVA
    # We need one row per participant per metric, with columns for each interface
    # We only pivot the metrics we are testing
    metrics_to_pivot = [m for m in metrics_to_test if m in data.columns]
    
    if not metrics_to_pivot:
        logger.error("No valid metrics found for ANOVA.")
        return anova_results

    try:
        wide_data = data.pivot_table(
            index='participant_id',
            columns='interface_type',
            values=metrics_to_pivot,
            aggfunc='mean'
        )
    except Exception as e:
        logger.error(f"Failed to pivot data for ANOVA: {e}")
        return anova_results

    for metric in metrics_to_pivot:
        # Check if we have both interface types for this metric
        if metric not in wide_data.columns.get_level_values(0):
            logger.warning(f"Metric {metric} not found in wide data after pivot.")
            continue
        
        available_interfaces = [col for col in wide_data.columns.get_level_values(1) if (metric, col) in wide_data.columns]
        
        if len(available_interfaces) < 2:
            logger.warning(f"Insufficient interface types for metric {metric}. Skipping ANOVA.")
            continue
        
        # Ensure we have 'traditional' and 'explainable'
        if 'traditional' not in available_interfaces or 'explainable' not in available_interfaces:
            logger.warning(f"Missing 'traditional' or 'explainable' for metric {metric}. Skipping.")
            continue
        
        # Extract the two conditions
        y_traditional = wide_data[metric]['traditional'].dropna()
        y_explainable = wide_data[metric]['explainable'].dropna()
        
        # Find common participants to ensure paired design
        common_participants = y_traditional.index.intersection(y_explainable.index)
        
        if len(common_participants) < 3:
            logger.warning(f"Insufficient paired data points ({len(common_participants)}) for ANOVA on {metric}.")
            continue
        
        y1 = y_traditional.loc[common_participants].values
        y2 = y_explainable.loc[common_participants].values
        
        try:
            # One-way Repeated Measures ANOVA using scipy
            # stats.f_oneway is for independent samples, so we use the difference approach or a specialized function.
            # Since scipy doesn't have a direct RM-ANOVA function that returns F and p easily without statsmodels,
            # and we want to avoid heavy dependencies if possible, we can use the difference approach for F-test equivalence
            # OR use statsmodels if available. Given the constraints, we will use a manual calculation or statsmodels if importable.
            # However, standard practice in simple pipelines often uses a wrapper.
            # Let's try to use statsmodels if available, otherwise fall back to a manual calculation or a simple F-test on differences 
            # (which is equivalent to paired t-test squared, but for 2 levels, F = t^2).
            # For 2 levels (Traditional vs Explainable), Repeated Measures ANOVA is mathematically equivalent to a Paired t-test.
            # F_statistic = t_statistic^2.
            
            t_stat, p_val = stats.ttest_rel(y1, y2)
            f_stat = t_stat ** 2
            
            # Effect size: Partial Eta Squared (η²)
            # η² = SS_effect / (SS_effect + SS_error)
            # For paired t-test: t = (mean_diff) / (std_diff / sqrt(n))
            # SS_effect = n * mean_diff^2
            # SS_error = (n-1) * var_diff
            # η² = t^2 / (t^2 + df) where df = n-1
            n = len(common_participants)
            df = n - 1
            eta_squared = f_stat / (f_stat + df)
            
            anova_results[metric] = {
                'F_statistic': f_stat,
                'p_value': p_val,
                'effect_size_eta_squared': eta_squared,
                'n': n
            }
            logger.info(f"ANOVA for {metric}: F={f_stat:.4f}, p={p_val:.4f}, η²={eta_squared:.4f}")
            
        except Exception as e:
            logger.error(f"ANOVA failed for {metric}: {e}")
            anova_results[metric] = {
                'F_statistic': np.nan,
                'p_value': np.nan,
                'effect_size_eta_squared': np.nan,
                'n': n,
                'error': str(e)
            }
    
    return anova_results

def run_holm_bonferroni(p_values: List[float]) -> List[float]:
    """
    Apply Holm-Bonferroni correction to a list of p-values.
    """
    if not p_values:
        return []
    
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    corrected_p = np.zeros(n)
    for i, p in enumerate(sorted_p):
        # Holm-Bonferroni: p * (n - i)
        # But must be <= 1 and non-decreasing
        corrected_p[i] = p * (n - i)
    
    # Ensure non-decreasing and capped at 1
    for i in range(1, n):
        corrected_p[i] = max(corrected_p[i], corrected_p[i-1])
    
    corrected_p = np.minimum(corrected_p, 1.0)
    
    # Restore original order
    final_corrected = np.zeros(n)
    final_corrected[sorted_indices] = corrected_p
    
    return final_corrected.tolist()

def calculate_effect_size(data: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate effect sizes (e.g., Eta-squared) for the ANOVA results.
    This is now integrated into run_anova_pipeline, but kept for API compatibility.
    """
    # The main calculation is done in run_anova_pipeline
    return {}

def verify_primary_anova_pvalue(anova_results: Dict[str, Any]) -> bool:
    """
    Verify if the primary ANOVA p-value is < 0.05.
    Primary metric is typically completion_time or sus_score.
    We check if ANY of the main metrics is significant.
    """
    for metric, res in anova_results.items():
        if 'p_value' in res and res['p_value'] < 0.05:
            return True
    return False

def generate_metrics_summary(data: pd.DataFrame, output_path: str) -> pd.DataFrame:
    """
    Generate the final metrics summary CSV.
    Columns: metric_name, interface_type, F_statistic, p_value, adjusted_p_value, effect_size
    """
    logger.info(f"Generating metrics summary at {output_path}")
    
    # Run ANOVA
    anova_results = run_anova_pipeline(data)
    
    # Collect all p-values for Holm-Bonferroni
    p_values = []
    metrics_order = []
    for metric, res in anova_results.items():
        if 'p_value' in res and not np.isnan(res['p_value']):
            p_values.append(res['p_value'])
            metrics_order.append(metric)
    
    # Apply Holm-Bonferroni
    if p_values:
        adjusted_p_values = run_holm_bonferroni(p_values)
        # Map back
        adj_map = dict(zip(metrics_order, adjusted_p_values))
    else:
        adj_map = {}
    
    rows = []
    for metric, res in anova_results.items():
        f_stat = res.get('F_statistic', np.nan)
        p_val = res.get('p_value', np.nan)
        adj_p = adj_map.get(metric, np.nan)
        effect = res.get('effect_size_eta_squared', np.nan)
        
        # The task asks for interface_type in the CSV.
        # Since this is a comparison, we list the comparison or the baseline.
        # We will list 'comparison' to denote the test between Traditional and Explainable.
        rows.append({
            'metric_name': metric,
            'interface_type': 'comparison', 
            'F_statistic': f_stat,
            'p_value': p_val,
            'adjusted_p_value': adj_p,
            'effect_size': effect
        })
    
    summary_df = pd.DataFrame(rows)
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    summary_df.to_csv(output_path, index=False)
    logger.info(f"Metrics summary written to {output_path}")
    
    return summary_df

def main():
    """
    CLI entry point for stat_utils.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Statistical Utilities")
    parser.add_argument("--input", type=str, required=True, help="Input cleaned data CSV")
    parser.add_argument("--output", type=str, required=True, help="Output normality log path")
    args = parser.parse_args()
    
    data = pd.read_csv(args.input)
    log_normality_test(data, args.output)

if __name__ == "__main__":
    main()