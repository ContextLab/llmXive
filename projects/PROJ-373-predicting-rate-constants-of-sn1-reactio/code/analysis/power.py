import os
import sys
import json
import logging
import argparse
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# Import project utilities and models
from config import ensure_dirs
from utils.logger import get_logger

logger = get_logger(__name__)

# Constants for power analysis
DEFAULT_ALPHA = 0.05
DEFAULT_POWER = 0.80
DEFAULT_EFFECT_SIZE = 0.5  # Cohen's d equivalent for regression metrics

def load_model_metrics(metrics_path: Path) -> Dict[str, Any]:
    """
    Load the model metrics from the artifacts directory.
    Expects a JSON file containing R2 and MAE.
    """
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        return json.load(f)

def calculate_variance_from_metrics(metrics: Dict[str, Any], n_samples: int) -> float:
    """
    Estimate the variance of the residuals from the model metrics.
    We assume R2 = 1 - (SS_res / SS_tot).
    If we assume the target variable y has a standard deviation sigma_y,
    then Var(residuals) = (1 - R2) * Var(y).
    
    Since we don't have Var(y) directly, we can estimate the residual variance
    using the MAE and the assumption of a normal distribution (MAE ≈ 0.8 * StdDev).
    Alternatively, we can use the R2 and an estimated total variance.
    
    For this implementation, we will derive the residual variance (sigma^2)
    from the MAE, assuming a normal distribution of errors:
    MAE = sigma * sqrt(2/pi)  =>  sigma = MAE * sqrt(pi/2)
    """
    mae = metrics.get('mae')
    if mae is None:
        raise ValueError("MAE not found in metrics")
    
    # Estimate standard deviation of residuals
    # MAE = sigma * sqrt(2/pi)
    sigma_residuals = mae * math.sqrt(math.pi / 2.0)
    variance = sigma_residuals ** 2
    return variance

def calculate_mde(variance: float, n_samples: int, alpha: float = DEFAULT_ALPHA, power: float = DEFAULT_POWER) -> float:
    """
    Calculate the Minimum Detectable Effect (MDE) for a given sample size.
    MDE here is defined as the minimum difference in means (or effect size) 
    that can be detected with the specified power and alpha.
    
    Formula for two-sample t-test approximation (simplified for regression context):
    MDE = (Z_alpha + Z_beta) * sigma * sqrt(2/n)
    where Z_alpha is the critical value for alpha, Z_beta for power (1-beta).
    
    For a one-sample or regression coefficient context, we adapt the formula:
    MDE = (Z_alpha + Z_beta) * sigma / sqrt(n)
    
    We use the standard normal approximation for large n.
    """
    # Z-scores for alpha and power
    # z_alpha for two-tailed test: norm.ppf(1 - alpha/2)
    # z_beta for power: norm.ppf(power)
    # Since we don't want to import scipy.stats for a simple calculation,
    # we use approximations or hardcode common values, but let's try to be precise.
    # However, standard library doesn't have inverse CDF. 
    # We will use a simple approximation or hardcoded values for standard cases.
    
    # Standard approximations:
    # alpha = 0.05 -> Z = 1.96
    # power = 0.80 -> Z = 0.84
    
    z_alpha = 1.96 if alpha == 0.05 else 2.576 # 0.01
    z_beta = 0.84 if power == 0.80 else 1.28 # 0.90
    
    # Adjust for two-tailed if necessary, but standard power analysis for effect size
    # usually uses Z_alpha/2 for two-tailed. Let's assume two-tailed.
    if alpha == 0.05:
        z_alpha = 1.96
    elif alpha == 0.01:
        z_alpha = 2.576
    
    if power == 0.80:
        z_beta = 0.84
    elif power == 0.90:
        z_beta = 1.28

    # MDE formula: (Z_alpha + Z_beta) * sigma / sqrt(n)
    # This gives the minimum detectable difference in the mean of the effect.
    # In regression, this translates to the minimum detectable change in R2 or coefficient.
    mde = (z_alpha + z_beta) * math.sqrt(variance) / math.sqrt(n_samples)
    return mde

def calculate_required_sample_size(variance: float, effect_size: float, alpha: float = DEFAULT_ALPHA, power: float = DEFAULT_POWER) -> int:
    """
    Calculate the required sample size to detect a given effect size with specified power.
    n = ((Z_alpha + Z_beta) * sigma / effect_size)^2
    """
    z_alpha = 1.96 if alpha == 0.05 else 2.576
    z_beta = 0.84 if power == 0.80 else 1.28

    n = ((z_alpha + z_beta) * math.sqrt(variance) / effect_size) ** 2
    return int(math.ceil(n))

def run_power_analysis(metrics_path: Path, output_path: Path, effect_size: float = DEFAULT_EFFECT_SIZE) -> None:
    """
    Main function to run the power analysis.
    1. Load model metrics.
    2. Estimate variance from MAE.
    3. Calculate MDE based on current sample size.
    4. Calculate required sample size for a target effect size.
    5. Generate a report CSV.
    """
    logger.info(f"Loading metrics from {metrics_path}")
    metrics = load_model_metrics(metrics_path)
    
    # Determine current sample size from the model artifacts or config
    # If not directly available, we might need to load the test set or infer from the training log.
    # For this task, we assume we can get the sample size from the metrics file if present,
    # or we need to load the data. The task says "based on observed variance", which implies
    # we use the current dataset size.
    # Let's assume the metrics file might contain 'n_samples' or we load the test set.
    # If not, we'll try to load the processed test set.
    
    n_samples = metrics.get('n_samples')
    if n_samples is None:
        # Fallback: Try to load the test set if path is known or infer from data
        # Since we don't have a direct path here, we assume the metrics file should have it
        # or we raise an error if it's missing.
        # However, to be robust, let's try to find the test set path from config if needed.
        # For now, we'll assume the metrics file has 'n_samples' or we use a default placeholder
        # and log a warning. But the task requires real data.
        # Let's assume the metrics file is generated by T022 and contains 'n_samples'.
        raise ValueError("n_samples not found in metrics. Please ensure T022 saves it.")

    logger.info(f"Current sample size: {n_samples}")
    
    variance = calculate_variance_from_metrics(metrics, n_samples)
    logger.info(f"Estimated residual variance: {variance}")
    
    mde = calculate_mde(variance, n_samples)
    required_n = calculate_required_sample_size(variance, effect_size)
    
    logger.info(f"Minimum Detectable Effect (MDE): {mde}")
    logger.info(f"Required sample size for effect size {effect_size}: {required_n}")
    
    # Prepare report data
    report_data = [
        {
            "parameter": "alpha",
            "value": DEFAULT_ALPHA,
            "description": "Significance level"
        },
        {
            "parameter": "power",
            "value": DEFAULT_POWER,
            "description": "Statistical power (1 - beta)"
        },
        {
            "parameter": "current_sample_size",
            "value": n_samples,
            "description": "Number of samples in the current test set"
        },
        {
            "parameter": "residual_variance",
            "value": variance,
            "description": "Estimated variance of model residuals"
        },
        {
            "parameter": "minimum_detectable_effect",
            "value": mde,
            "description": "Smallest effect size detectable with current sample size"
        },
        {
            "parameter": "target_effect_size",
            "value": effect_size,
            "description": "Target effect size for sample size calculation"
        },
        {
            "parameter": "required_sample_size",
            "value": required_n,
            "description": "Sample size needed to detect the target effect size"
        },
        {
            "parameter": "current_power_for_target_effect",
            "value": "N/A", # Could calculate if needed, but we'll skip for simplicity
            "description": "Current power to detect target effect (optional)"
        }
    ]
    
    # Create output directory if it doesn't exist
    ensure_dirs()
    
    # Write CSV
    df = pd.DataFrame(report_data)
    df.to_csv(output_path, index=False)
    logger.info(f"Power analysis report saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run power analysis for SN1 rate constant prediction model.")
    parser.add_argument("--metrics-path", type=str, default="artifacts/metrics.json",
                        help="Path to the model metrics JSON file.")
    parser.add_argument("--output-path", type=str, default="artifacts/power_analysis_report.csv",
                        help="Path to save the power analysis report CSV.")
    parser.add_argument("--effect-size", type=float, default=DEFAULT_EFFECT_SIZE,
                        help="Target effect size for sample size calculation.")
    
    args = parser.parse_args()
    
    metrics_path = Path(args.metrics_path)
    output_path = Path(args.output_path)
    
    try:
        run_power_analysis(metrics_path, output_path, args.effect_size)
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
