"""
T027b: MMSE Robustness Analysis

Re-runs the statistical analysis (Welch's t-test, effect sizes) on the dataset
that has NOT been filtered by MMSE scores (cleaned_dataset_no_mmse.csv).

This allows comparison of the primary results (with MMSE filter) vs. robustness
results (without MMSE filter) to determine if cognitive impairment exclusions
significantly alter the findings.

Output: data/results/robustness_report.json
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

# Import analysis functions from the main analysis module
from code.analysis import welch_t_test, calculate_cohen_d, calculate_effect_size_ci, bonferroni_correction

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "cleaned_dataset_no_mmse.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "results" / "robustness_report.json"
MMSE_THRESHOLD = 24

def load_no_mmse_dataset() -> pd.DataFrame:
    """Load the dataset that was NOT filtered by MMSE."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Required input file missing: {INPUT_FILE}. "
            "Ensure T012e/T027a has been completed to generate cleaned_dataset_no_mmse.csv."
        )
    
    df = pd.read_csv(INPUT_FILE)
    logger.info(f"Loaded {len(df)} records from {INPUT_FILE}")
    
    # Validate required columns
    required_cols = ['participant_id', 'stimulus_type', 'perseverative_errors', 
                    'categories_completed', 'age']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    return df

def run_robustness_analysis(df: pd.DataFrame) -> dict:
    """
    Run Welch's t-test and effect size calculations on the no-MMSE dataset.
    
    Returns a dictionary with statistical results for both metrics.
    """
    results = {
        'dataset': str(INPUT_FILE.relative_to(PROJECT_ROOT)),
        'sample_size': len(df),
        'analysis_type': 'robustness_check_no_mmse_filter',
        'metrics': {}
    }
    
    # Ensure we have both conditions
    nostalgia_group = df[df['stimulus_type'] == 'nostalgia']
    control_group = df[df['stimulus_type'] == 'control']
    
    if len(nostalgia_group) < 2 or len(control_group) < 2:
        raise ValueError("Insufficient sample size for one or both groups after filtering.")
    
    logger.info(f"Nostalgia group: {len(nostalgia_group)}, Control group: {len(control_group)}")
    
    # Analyze Perseverative Errors
    logger.info("Analyzing Perseverative Errors...")
    errors_nostalgia = nostalgia_group['perseverative_errors'].dropna()
    errors_control = control_group['perseverative_errors'].dropna()
    
    if len(errors_nostalgia) < 2 or len(errors_control) < 2:
        logger.warning("Insufficient data for Perseverative Errors analysis")
        results['metrics']['perseverative_errors'] = {
            'status': 'skipped',
            'reason': 'insufficient_data'
        }
    else:
        # Welch's t-test
        t_stat, p_val = welch_t_test(errors_nostalgia, errors_control)
        
        # Effect size (Cohen's d)
        cohens_d = calculate_cohen_d(errors_nostalgia, errors_control)
        ci_low, ci_high = calculate_effect_size_ci(errors_nostalgia, errors_control, cohens_d)
        
        results['metrics']['perseverative_errors'] = {
            'status': 'success',
            't_statistic': float(t_stat),
            'p_value': float(p_val),
            'cohens_d': float(cohens_d),
            'ci_95': [float(ci_low), float(ci_high)],
            'nostalgia_mean': float(errors_nostalgia.mean()),
            'nostalgia_std': float(errors_nostalgia.std()),
            'nostalgia_n': int(len(errors_nostalgia)),
            'control_mean': float(errors_control.mean()),
            'control_std': float(errors_control.std()),
            'control_n': int(len(errors_control))
        }
        logger.info(f"  Perseverative Errors: t={t_stat:.4f}, p={p_val:.4f}, d={cohens_d:.4f}")
    
    # Analyze Categories Completed
    logger.info("Analyzing Categories Completed...")
    cats_nostalgia = nostalgia_group['categories_completed'].dropna()
    cats_control = control_group['categories_completed'].dropna()
    
    if len(cats_nostalgia) < 2 or len(cats_control) < 2:
        logger.warning("Insufficient data for Categories Completed analysis")
        results['metrics']['categories_completed'] = {
            'status': 'skipped',
            'reason': 'insufficient_data'
        }
    else:
        # Welch's t-test
        t_stat, p_val = welch_t_test(cats_nostalgia, cats_control)
        
        # Effect size (Cohen's d)
        cohens_d = calculate_cohen_d(cats_nostalgia, cats_control)
        ci_low, ci_high = calculate_effect_size_ci(cats_nostalgia, cats_control, cohens_d)
        
        results['metrics']['categories_completed'] = {
            'status': 'success',
            't_statistic': float(t_stat),
            'p_value': float(p_val),
            'cohens_d': float(cohens_d),
            'ci_95': [float(ci_low), float(ci_high)],
            'nostalgia_mean': float(cats_nostalgia.mean()),
            'nostalgia_std': float(cats_nostalgia.std()),
            'nostalgia_n': int(len(cats_nostalgia)),
            'control_mean': float(cats_control.mean()),
            'control_std': float(cats_control.std()),
            'control_n': int(len(cats_control))
        }
        logger.info(f"  Categories Completed: t={t_stat:.4f}, p={p_val:.4f}, d={cohens_d:.4f}")
    
    # Apply Bonferroni correction for the two metrics
    logger.info("Applying Bonferroni correction...")
    p_values = []
    for metric_name, metric_data in results['metrics'].items():
        if metric_data.get('status') == 'success':
            p_values.append(metric_data['p_value'])
    
    if len(p_values) > 0:
        corrected_p_values = bonferroni_correction(p_values)
        for i, metric_name in enumerate(results['metrics']):
            if results['metrics'][metric_name].get('status') == 'success':
                results['metrics'][metric_name]['p_value_bonferroni'] = float(corrected_p_values[i])
                logger.info(f"  {metric_name} corrected p-value: {corrected_p_values[i]:.4f}")
    
    return results

def save_report(results: dict):
    """Save the robustness report to JSON."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Robustness report saved to {OUTPUT_FILE}")

def main():
    """Main entry point for T027b."""
    logger.info("Starting T027b: MMSE Robustness Analysis")
    
    try:
        # Load dataset without MMSE filter
        df = load_no_mmse_dataset()
        
        # Run analysis
        results = run_robustness_analysis(df)
        
        # Save results
        save_report(results)
        
        logger.info("T027b completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())