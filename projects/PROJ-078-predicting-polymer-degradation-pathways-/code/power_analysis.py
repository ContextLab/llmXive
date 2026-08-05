import logging
import os
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

from utils import get_logger, get_project_paths

def calculate_cohen_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """Calculate Cohen's d effect size."""
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1), np.std(group2)
    pooled_std = math.sqrt((std1**2 + std2**2) / 2)
    if pooled_std == 0:
        return 0.0
    return (mean1 - mean2) / pooled_std

def interpret_effect_size(d: float) -> str:
    """Interpret Cohen's d."""
    if abs(d) < 0.2:
        return "negligible"
    elif abs(d) < 0.5:
        return "small"
    elif abs(d) < 0.8:
        return "medium"
    else:
        return "large"

def check_dataset_power(n: int, effect_size: float = 0.5, alpha: float = 0.05, power: float = 0.8) -> Tuple[int, str]:
    """
    Estimate required sample size for a given effect size and power.
    Using a simplified approximation for two-sample t-test.
    """
    # Approximation: n = 2 * ((Z_alpha + Z_beta) / effect_size)^2
    # Z_alpha for 0.05 (two-tailed) is ~1.96
    # Z_beta for 0.8 power is ~0.84
    z_alpha = 1.96
    z_beta = 0.84
    required_n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    return int(math.ceil(required_n))

def run_power_analysis_from_csv(input_path: str):
    """
    Run power analysis on the dataset and save results.
    """
    logger = get_logger()
    paths = get_project_paths()
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        # Save error state
        error_log = paths['state'] / 'power_analysis_error.json'
        with open(str(error_log), 'w') as f:
            json.dump({'error': 'Input file not found', 'path': input_path}, f)
        return
    
    df = pd.read_csv(input_path)
    n = len(df)
    
    if n == 0:
        logger.error("Dataset is empty.")
        error_log = paths['state'] / 'power_analysis_error.json'
        with open(str(error_log), 'w') as f:
            json.dump({'error': 'Dataset is empty'}, f)
        return
    
    # For this analysis, we assume a binary classification problem (e.g., hydrolysis vs other)
    # We'll estimate effect size based on a heuristic or assume a medium effect size (0.5)
    # In a real scenario, we would calculate effect size from the data if labels are numeric.
    # Since degradation_pathway is categorical, we'll use a default effect size.
    effect_size = 0.5 # Medium effect size assumption
    
    required_n, _ = check_dataset_power(n, effect_size)
    
    # Determine action
    action = "none"
    if n < 50:
        action = "augment_aggressive"
    elif n < 150:
        action = "augment"
    
    # Save augmentation trigger
    trigger_path = paths['state'] / 'augmentation_trigger.json'
    trigger_data = {
        'n': n,
        'required_n': required_n,
        'action': action,
        'effect_size_assumed': effect_size
    }
    with open(str(trigger_path), 'w') as f:
        json.dump(trigger_data, f, indent=2)
    
    logger.info(f"Power analysis complete. n={n}, required_n={required_n}, action={action}")
    
    # Save report
    report_path = paths['reports'] / 'power_analysis_report.json'
    report_data = {
        'n': n,
        'required_n': required_n,
        'warning': 'true' if n < 150 else 'false',
        'action': action
    }
    with open(str(report_path), 'w') as f:
        json.dump(report_data, f, indent=2)
    
    # If action is augment, create warning text file
    if action != "none":
        warning_path = paths['reports'] / 'power_analysis_warning.txt'
        with open(str(warning_path), 'w') as f:
            f.write(f"Power Analysis Warning: Dataset size n={n} is below the recommended threshold of 150.\n")
            f.write(f"Action triggered: {action}\n")
            f.write(f"Estimated required sample size for medium effect size: {required_n}\n")
        logger.info(f"Saved warning to {warning_path}")

def main():
    """Main entry point."""
    paths = get_project_paths()
    input_path = paths['processed'] / 'processed_graph_dataset.csv'
    run_power_analysis_from_csv(str(input_path))

if __name__ == '__main__':
    main()
