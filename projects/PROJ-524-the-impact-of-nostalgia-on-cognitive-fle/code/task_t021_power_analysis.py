"""
Task T021: Calculate statistical power and Minimum Detectable Effect Size (MDES).

This module computes statistical power and MDES for the observed effects
in the nostalgia vs control group comparison, and appends these values
to the statistical report.

Dependencies: T020 (effect sizes), T018 (Welch's t-test)
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Import from sibling modules as per API surface
from config import get_config, get_env_float
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp
from statsmodels.stats.power import tt_ind_solve_power
from statsmodels.stats.effect_size import CoeffCohensD

# Configure logging
logger = setup_logging("T021_power_analysis")

def load_cleaned_dataset() -> pd.DataFrame:
    """Load the cleaned dataset from data/processed/cleaned_dataset.csv."""
    config = get_config()
    cleaned_path = config['paths']['cleaned_dataset']
    
    if not os.path.exists(cleaned_path):
        raise FileNotFoundError(f"Cleaned dataset not found at {cleaned_path}. "
                              "Ensure T014a has completed successfully.")
    
    df = pd.read_csv(cleaned_path)
    logger.info(f"Loaded cleaned dataset with {len(df)} records from {cleaned_path}")
    return df

def load_statistical_report() -> Dict[str, Any]:
    """Load the statistical report from data/results/statistical_report.json."""
    config = get_config()
    report_path = config['paths']['results_dir'] / 'statistical_report.json'
    
    if not os.path.exists(report_path):
        raise FileNotFoundError(f"Statistical report not found at {report_path}. "
                              "Ensure T020 has completed successfully.")
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    logger.info(f"Loaded statistical report from {report_path}")
    return report

def save_statistical_report(report: Dict[str, Any]) -> None:
    """Save the updated statistical report to data/results/statistical_report.json."""
    config = get_config()
    report_path = config['paths']['results_dir'] / 'statistical_report.json'
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Saved updated statistical report to {report_path}")

def calculate_power_and_mdes(
    group1_n: int,
    group2_n: int,
    effect_size: float,
    alpha: float = 0.05
) -> Dict[str, float]:
    """
    Calculate statistical power and Minimum Detectable Effect Size (MDES).
    
    Parameters:
    -----------
    group1_n : int
        Sample size of the first group (nostalgia)
    group2_n : int
        Sample size of the second group (control)
    effect_size : float
        Observed Cohen's d effect size
    alpha : float
        Significance level (default 0.05)
    
    Returns:
    --------
    Dict with 'statistical_power' and 'minimum_detectable_effect_size'
    """
    # Calculate statistical power for the observed effect
    # Using tt_ind_solve_power with effect_size, nobs1, ratio, alpha
    n_obs1 = group1_n
    n_obs2 = group2_n
    ratio = n_obs2 / n_obs1 if n_obs2 > 0 else 1.0
    
    try:
        # Solve for power given effect_size, sample sizes, and alpha
        power = tt_ind_solve_power(
            effect_size=abs(effect_size),
            nobs1=n_obs1,
            ratio=ratio,
            alpha=alpha,
            alternative='two-sided'
        )
    except Exception as e:
        log_warning(f"Power calculation failed for effect size {effect_size}: {e}")
        power = 0.0
    
    # Calculate Minimum Detectable Effect Size (MDES)
    # Solve for effect_size given power=0.8 (standard), sample sizes, and alpha
    target_power = 0.8
    try:
        mdes = tt_ind_solve_power(
            effect_size=None,
            nobs1=n_obs1,
            ratio=ratio,
            alpha=alpha,
            power=target_power,
            alternative='two-sided'
        )
    except Exception as e:
        log_warning(f"MDES calculation failed: {e}")
        mdes = 0.0
    
    return {
        'statistical_power': float(power),
        'minimum_detectable_effect_size': float(mdes),
        'alpha': alpha,
        'sample_size_nostalgia': group1_n,
        'sample_size_control': group2_n
    }

def run_power_analysis(
    report: Dict[str, Any],
    df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Run power analysis for all comparisons in the report and update with power/MDES.
    
    Parameters:
    -----------
    report : Dict
        Statistical report containing comparison results
    df : pd.DataFrame
        Cleaned dataset for reference (not directly used in calculation, 
        but available for future extensions)
    
    Returns:
    --------
    Updated report with power analysis results appended
    """
    alpha = get_env_float('ALPHA_LEVEL', 0.05)
    logger.info(f"Running power analysis with alpha={alpha}")
    
    comparisons = report.get('comparisons', [])
    updated_comparisons = []
    power_values = []
    mdes_values = []
    significant_count_alpha05 = 0
    significant_count_alpha01 = 0
    
    for comp in comparisons:
        metric = comp.get('metric', 'unknown')
        group_nostalgia = comp.get('group_nostalgia', {})
        group_control = comp.get('group_control', {})
        effect_size_data = comp.get('effect_size', {})
        
        n_nostalgia = group_nostalgia.get('n', 0)
        n_control = group_control.get('n', 0)
        cohen_d = effect_size_data.get('cohen_d', 0.0)
        p_value_corrected = comp.get('p_value_corrected', 1.0)
        
        # Calculate power and MDES
        power_result = calculate_power_and_mdes(
            group1_n=n_nostalgia,
            group2_n=n_control,
            effect_size=cohen_d,
            alpha=alpha
        )
        
        # Update comparison with power analysis results
        comp['power_analysis'] = power_result
        updated_comparisons.append(comp)
        
        # Collect metrics for summary
        power_values.append(power_result['statistical_power'])
        mdes_values.append(power_result['minimum_detectable_effect_size'])
        
        # Count significant results
        if p_value_corrected < 0.05:
            significant_count_alpha05 += 1
        if p_value_corrected < 0.01:
            significant_count_alpha01 += 1
        
        log_info(f"Power analysis for {metric}: power={power_result['statistical_power']:.3f}, "
                f"MDES={power_result['minimum_detectable_effect_size']:.3f}")
    
    # Update summary section
    report['comparisons'] = updated_comparisons
    report['summary'] = {
        'total_comparisons': len(comparisons),
        'significant_at_alpha_05': significant_count_alpha05,
        'significant_at_alpha_01': significant_count_alpha01,
        'average_power': float(np.mean(power_values)) if power_values else 0.0,
        'average_mdes': float(np.mean(mdes_values)) if mdes_values else 0.0
    }
    
    logger.info(f"Power analysis complete: avg_power={report['summary']['average_power']:.3f}, "
               f"avg_mdes={report['summary']['average_mdes']:.3f}")
    
    return report

def main():
    """Main entry point for T021 power analysis."""
    logger.info(f"Starting T021 power analysis at {get_timestamp()}")
    
    try:
        # Load required data
        df = load_cleaned_dataset()
        report = load_statistical_report()
        
        # Run power analysis
        updated_report = run_power_analysis(report, df)
        
        # Save updated report
        save_statistical_report(updated_report)
        
        logger.info(f"T021 power analysis completed successfully at {get_timestamp()}")
        return 0
        
    except FileNotFoundError as e:
        log_error(f"Required file not found: {e}")
        return 1
    except Exception as e:
        log_error(f"Power analysis failed: {e}")
        raise

if __name__ == "__main__":
    exit(main())
