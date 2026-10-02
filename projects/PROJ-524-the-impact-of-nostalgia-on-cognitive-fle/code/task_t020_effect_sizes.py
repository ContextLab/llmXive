"""
T020: Calculate and report Cohen's d with 95% confidence intervals for all primary comparisons.

This script implements the effect size calculation logic required for User Story 2.
It reads the cleaned dataset, groups by stimulus type, and computes Cohen's d
for 'perseverative_errors' and 'categories_completed' using statsmodels.
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from statsmodels.stats.weightstats import _tconfint_generic
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
INPUT_FILE = DATA_PROCESSED_DIR / "final_cleaned_dataset.csv"
OUTPUT_FILE = DATA_RESULTS_DIR / "effect_sizes.json"

def load_cleaned_dataset():
    """Load the final cleaned dataset."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Required input file not found: {INPUT_FILE}")
    
    df = pd.read_csv(INPUT_FILE)
    
    # Ensure required columns exist
    required_cols = ['participant_id', 'stimulus_type', 'perseverative_errors', 'categories_completed', 'age']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input data: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} records from {INPUT_FILE}")
    return df

def calculate_cohen_d(group1, group2):
    """
    Calculate Cohen's d for two independent groups.
    Uses pooled standard deviation.
    """
    n1, n2 = len(group1), len(group2)
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    # Handle zero variance cases
    if var1 == 0 and var2 == 0:
        return 0.0, 0.0, 0.0 # d, ci_lower, ci_upper
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0, 0.0, 0.0
    
    d = (mean1 - mean2) / pooled_std
    
    # Calculate 95% CI for Cohen's d
    # Using non-central t-distribution approximation or standard error method
    # Standard Error of d
    # SE_d = sqrt((n1 + n2)/(n1*n2) + d^2/(2*(n1+n2)))
    se_d = np.sqrt((n1 + n2) / (n1 * n2) + (d**2) / (2 * (n1 + n2)))
    
    # Critical t-value for 95% CI (approximate with normal for large N, or use t-distribution)
    # Degrees of freedom
    df = n1 + n2 - 2
    t_crit = stats.t.ppf(0.975, df)
    
    ci_lower = d - t_crit * se_d
    ci_upper = d + t_crit * se_d
    
    return d, ci_lower, ci_upper

def calculate_effect_sizes(df, metric_name):
    """Calculate effect sizes for a specific metric between nostalgia and control groups."""
    if metric_name not in df.columns:
        logger.warning(f"Metric {metric_name} not found in dataframe")
        return None
    
    # Filter out NaN values for this metric
    valid_df = df.dropna(subset=['stimulus_type', metric_name])
    
    if valid_df.empty:
        logger.warning(f"No valid data for {metric_name}")
        return None
    
    # Group by stimulus_type
    # We assume 'nostalgia' and 'control' are the two groups
    nostalgia_group = valid_df[valid_df['stimulus_type'] == 'nostalgia'][metric_name].values
    control_group = valid_df[valid_df['stimulus_type'] == 'control'][metric_name].values
    
    if len(nostalgia_group) < 2 or len(control_group) < 2:
        logger.warning(f"Insufficient sample size for {metric_name} (N_nostalgia={len(nostalgia_group)}, N_control={len(control_group)})")
        return None
    
    d, ci_lower, ci_upper = calculate_cohen_d(nostalgia_group, control_group)
    
    return {
        "metric": metric_name,
        "n_nostalgia": int(len(nostalgia_group)),
        "n_control": int(len(control_group)),
        "mean_nostalgia": float(np.mean(nostalgia_group)),
        "mean_control": float(np.mean(control_group)),
        "cohens_d": float(d),
        "ci_95_lower": float(ci_lower),
        "ci_95_upper": float(ci_upper)
    }

def run_effect_size_analysis(df):
    """Run effect size analysis for all primary metrics."""
    metrics = ['perseverative_errors', 'categories_completed']
    results = {}
    
    for metric in metrics:
        logger.info(f"Calculating effect size for {metric}...")
        effect_result = calculate_effect_sizes(df, metric)
        if effect_result:
            results[metric] = effect_result
        else:
            results[metric] = {
                "metric": metric,
                "status": "skipped",
                "reason": "Insufficient data or sample size"
            }
    
    return results

def save_results(results):
    """Save effect size results to JSON file."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "task": "T020",
        "description": "Effect Size Analysis (Cohen's d with 95% CI)",
        "input_file": str(INPUT_FILE),
        "results": results
    }
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Saved effect size results to {OUTPUT_FILE}")

def main():
    """Main entry point for T020."""
    try:
        logger.info("Starting T020: Effect Size Analysis")
        
        # Load data
        df = load_cleaned_dataset()
        
        # Run analysis
        results = run_effect_size_analysis(df)
        
        # Save results
        save_results(results)
        
        logger.info("T020 completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())
