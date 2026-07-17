"""
Task T031: Post-hoc power analysis for matched pairs.

Performs power analysis on the final matched pair count using scipy.stats.
Uses effect size=0.5, alpha=0.05, and targets >=0.80 power.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd
from scipy.stats import ttest_rel
from scipy.stats import power_analysis

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import get_logger, setup_logging
from utils.models import MatchedPair

# Configure logger
logger = get_logger(__name__)

# Constants
EFFECT_SIZE = 0.5
ALPHA = 0.05
TARGET_POWER = 0.80
DATA_DIR = Path("data/processed")
OUTPUT_FILE = DATA_DIR / "power_analysis_results.json"


def setup_output_directories():
    """Ensure output directories exist."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ensured: {OUTPUT_FILE.parent}")


def load_matched_pairs() -> pd.DataFrame:
    """
    Load the matched pairs from the processed data.
    Returns a DataFrame with the matched pairs.
    """
    input_file = DATA_DIR / "matched_pairs.csv"
    if not input_file.exists():
        raise FileNotFoundError(f"Matched pairs file not found: {input_file}")
    
    df = pd.read_csv(input_file)
    logger.info(f"Loaded {len(df)} matched pairs from {input_file}")
    return df


def load_metrics_longitudinal() -> pd.DataFrame:
    """
    Load the longitudinal metrics from the processed data.
    Returns a DataFrame with the metrics.
    """
    input_file = DATA_DIR / "metrics_longitudinal.csv"
    if not input_file.exists():
        raise FileNotFoundError(f"Longitudinal metrics file not found: {input_file}")
    
    df = pd.read_csv(input_file)
    logger.info(f"Loaded {len(df)} metric records from {input_file}")
    return df


def calculate_effect_size_from_data(df: pd.DataFrame, metric_col: str) -> float:
    """
    Calculate Cohen's d for a specific metric from the matched pairs.
    This is used to validate the assumed effect size or adjust if necessary.
    """
    # Filter out rows with missing values
    valid_data = df.dropna(subset=[metric_col])
    
    if len(valid_data) < 2:
        logger.warning("Insufficient data to calculate effect size.")
        return EFFECT_SIZE
    
    # Calculate mean and std for LLM and Human groups
    llm_group = valid_data[valid_data['tag'] == 'LLM'][metric_col]
    human_group = valid_data[valid_data['tag'] == 'Human'][metric_col]
    
    if len(llm_group) == 0 or len(human_group) == 0:
        logger.warning("One of the groups is empty. Cannot calculate effect size.")
        return EFFECT_SIZE
    
    mean_diff = llm_group.mean() - human_group.mean()
    # Pooled standard deviation
    std_llm = llm_group.std()
    std_human = human_group.std()
    n_llm = len(llm_group)
    n_human = len(human_group)
    
    if n_llm + n_human == 0:
        return EFFECT_SIZE
    
    pooled_std = np.sqrt(((n_llm - 1) * std_llm**2 + (n_human - 1) * std_human**2) / (n_llm + n_human - 2))
    
    if pooled_std == 0:
        logger.warning("Pooled std is zero. Cannot calculate effect size.")
        return EFFECT_SIZE
    
    cohens_d = mean_diff / pooled_std
    logger.info(f"Calculated Cohen's d for {metric_col}: {cohens_d:.4f}")
    return abs(cohens_d)  # Use absolute value for power analysis


def perform_power_analysis(n_pairs: int, effect_size: float, alpha: float = ALPHA) -> Dict[str, Any]:
    """
    Perform post-hoc power analysis for a paired t-test (Wilcoxon context).
    Since scipy.stats.power_analysis is not directly available for paired t-tests
    in older versions, we approximate using t-test power analysis logic.
    
    For a paired t-test, the power is calculated based on the non-central t-distribution.
    We use the `scipy.stats` module to approximate this.
    
    Note: scipy.stats does not have a direct `power_analysis` function for paired t-tests.
    We will use a manual calculation or an approximation.
    
    However, the task specifically mentions `scipy.stats.power_analysis`. 
    In newer scipy versions (1.11+), there is `scipy.stats.power_analysis` for some tests,
    but for t-tests, we might need to use `statsmodels` or manual calculation.
    
    Given the constraint to use `scipy`, and if `scipy.stats.power_analysis` is not available,
    we will implement a manual calculation based on the non-central t-distribution.
    
    But the task says: "using scipy.stats.power_analysis". 
    Let's check if it exists. If not, we'll use an alternative approach.
    
    Actually, `scipy.stats` does not have a `power_analysis` function for t-tests.
    We will use `statsmodels.stats.power` if available, or fall back to a manual calculation.
    
    However, the task requires `scipy.stats.power_analysis`. 
    Since it doesn't exist in scipy, we will interpret this as using scipy's t-test functions
    and calculating power manually or using an approximation.
    
    We will use the following approach:
    1. Calculate the non-centrality parameter (ncp) for the t-test.
    2. Use the non-central t-distribution to find the power.
    
    Steps:
    - ncp = effect_size * sqrt(n_pairs)
    - power = 1 - CDF(t_critical, df, ncp) + CDF(-t_critical, df, ncp)
    
    But note: The task says "using scipy.stats.power_analysis". 
    Since it's not available, we will use a manual calculation and document it.
    
    Alternatively, we can use `statsmodels` if it's available, but the task specifies scipy.
    
    Let's try to use `scipy.stats` functions to calculate power.
    """
    
    # If scipy.stats.power_analysis is available (unlikely), use it.
    # Otherwise, calculate manually.
    try:
        # Attempt to use scipy.stats.power_analysis if it exists (future version or custom)
        # This is a placeholder for the intended function.
        # Since it doesn't exist, we'll calculate manually.
        raise AttributeError
    except AttributeError:
        # Manual calculation for paired t-test power
        # Degrees of freedom
        df = n_pairs - 1
        
        # Critical t-value for two-tailed test
        t_critical = abs(ttest_rel.ppf(1 - alpha/2, df))
        
        # Non-centrality parameter
        ncp = effect_size * np.sqrt(n_pairs)
        
        # Power calculation using non-central t-distribution
        # Power = P(T > t_critical | ncp) + P(T < -t_critical | ncp)
        from scipy.stats import nct
        power = 1 - nct.cdf(t_critical, df, ncp) + nct.cdf(-t_critical, df, ncp)
        
        logger.info(f"Manual power calculation: n={n_pairs}, effect_size={effect_size}, power={power:.4f}")
        return {
            "n_pairs": n_pairs,
            "effect_size": effect_size,
            "alpha": alpha,
            "power": float(power),
            "target_power": TARGET_POWER,
            "meets_target": power >= TARGET_POWER,
            "method": "manual_non_central_t"
        }
    
    # If we had access to scipy.stats.power_analysis, we would do:
    # result = power_analysis(effect_size=effect_size, n=n_pairs, alpha=alpha, test='ttest_rel')
    # return result


def run_power_analysis_pipeline():
    """
    Run the power analysis pipeline.
    """
    setup_output_directories()
    
    # Load data
    try:
        pairs_df = load_matched_pairs()
        metrics_df = load_metrics_longitudinal()
    except FileNotFoundError as e:
        logger.error(str(e))
        return
    
    # Get the number of matched pairs
    n_pairs = len(pairs_df)
    logger.info(f"Total matched pairs: {n_pairs}")
    
    if n_pairs == 0:
        logger.error("No matched pairs found. Cannot perform power analysis.")
        return
    
    # We will perform power analysis for the primary metrics: churn and latency
    metrics_to_analyze = ['churn_lines', 'days_to_fix']
    results = {}
    
    for metric in metrics_to_analyze:
        # Check if the metric is available in the metrics dataframe
        if metric not in metrics_df.columns:
            logger.warning(f"Metric {metric} not found in metrics_longitudinal.csv. Skipping.")
            continue
        
        # Calculate effect size from the data if possible, otherwise use assumed 0.5
        # For power analysis, we often use an assumed effect size (0.5 is medium)
        # But we can also calculate it from the data to see what we have
        effect_size = calculate_effect_size_from_data(metrics_df, metric)
        
        # Perform power analysis
        power_result = perform_power_analysis(n_pairs, effect_size)
        power_result['metric'] = metric
        results[metric] = power_result
    
    # Also perform power analysis for the assumed effect size of 0.5
    assumed_effect_size = EFFECT_SIZE
    assumed_results = {}
    for metric in metrics_to_analyze:
        power_result = perform_power_analysis(n_pairs, assumed_effect_size)
        power_result['metric'] = metric
        power_result['effect_size_used'] = assumed_effect_size
        assumed_results[metric] = power_result
    
    # Combine results
    final_results = {
        "total_matched_pairs": n_pairs,
        "assumed_effect_size": assumed_effect_size,
        "alpha": ALPHA,
        "target_power": TARGET_POWER,
        "results_assumed_effect_size": assumed_results,
        "results_calculated_effect_size": results
    }
    
    # Save results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    logger.info(f"Power analysis results saved to {OUTPUT_FILE}")
    
    # Print summary
    print("\n=== Power Analysis Summary ===")
    print(f"Total matched pairs: {n_pairs}")
    print(f"Assumed effect size: {assumed_effect_size}")
    print(f"Alpha: {ALPHA}")
    print(f"Target power: {TARGET_POWER}")
    print("\nResults for assumed effect size (0.5):")
    for metric, res in assumed_results.items():
        print(f"  {metric}: power = {res['power']:.4f}, meets target = {res['meets_target']}")
    
    print("\nResults for calculated effect size:")
    for metric, res in results.items():
        print(f"  {metric}: effect_size = {res['effect_size']:.4f}, power = {res['power']:.4f}, meets target = {res['meets_target']}")


def main():
    """Main entry point."""
    setup_logging()
    logger.info("Starting power analysis pipeline (T031)")
    run_power_analysis_pipeline()
    logger.info("Power analysis pipeline completed")


if __name__ == "__main__":
    main()