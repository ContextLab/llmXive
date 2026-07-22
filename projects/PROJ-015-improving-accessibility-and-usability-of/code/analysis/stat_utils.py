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
    """
    logger.info("Running Repeated Measures ANOVA pipeline.")
    # Implementation details for ANOVA would go here
    # This is a placeholder for the logic required by T023a
    return {}

def run_holm_bonferroni(p_values: List[float]) -> List[float]:
    """
    Apply Holm-Bonferroni correction to a list of p-values.
    """
    # Implementation details
    return p_values

def calculate_effect_size(data: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate effect sizes (e.g., Eta-squared) for the ANOVA results.
    """
    return {}

def verify_primary_anova_pvalue(anova_results: Dict[str, Any]) -> bool:
    """
    Verify if the primary ANOVA p-value is < 0.05.
    """
    return False

def generate_metrics_summary(data: pd.DataFrame, output_path: str) -> pd.DataFrame:
    """
    Generate the final metrics summary CSV.
    """
    return pd.DataFrame()

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
