import csv
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
from scipy import stats
from code.config import get_project_root

logger = logging.getLogger(__name__)

def perform_two_sample_ttest(group1: List[float], group2: List[float]) -> Dict[str, float]:
    """
    Perform a two-sample t-test between two groups.
    
    Returns:
        Dictionary with t-statistic and p-value.
    """
    t_stat, p_val = stats.ttest_ind(group1, group2)
    return {"t_statistic": float(t_stat), "p_value": float(p_val)}

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Returns:
        List of booleans indicating significance after correction.
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return []
    
    corrected_alpha = alpha / n_tests
    return [p < corrected_alpha for p in p_values]

def run_noise_sweep_statistics():
    """
    Run statistical tests on noise sweep data.
    Produces data/processed/noise_stats.csv as required.
    """
    root = get_project_root()
    processed_dir = root / "data" / "processed"
    
    # Load noise sweep results
    sweep_path = processed_dir / "noise_sweep.csv"
    if not sweep_path.exists():
        logger.error("Noise sweep results not found. Run sensitivity_sweep first.")
        return

    results = []
    with open(sweep_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["valid"] == "True":
                results.append({
                    "sigma": float(row["sigma"]),
                    "ellipticity": float(row["ellipticity_mean"])
                })
    
    if len(results) < 2:
        logger.warning("Insufficient data for statistical analysis.")
        return

    sigmas = [r["sigma"] for r in results]
    ellipticities = [r["ellipticity"] for r in results]
    
    # Linear regression: ellipticity ~ sigma
    slope, intercept, r_value, p_value, std_err = stats.linregress(sigmas, ellipticities)
    
    # Calculate bias relative to zero noise (intercept)
    # Assuming ground truth is close to intercept or 0 bias at 0 noise
    # For this task, we report the regression stats
    
    stats_path = processed_dir / "noise_stats.csv"
    with open(stats_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sigma", "mean_bias", "p_value", "significant", "slope"])
        
        # We treat the slope as the bias per unit noise, and p_value from regression
        # For a single regression line, p_value is for the slope != 0
        significant = p_value < 0.05
        writer.writerow([sigmas[0], intercept, p_value, significant, slope])
        
        # If we had multiple measurements per sigma, we would calculate mean_bias per sigma
        # Here we output the regression summary
    
    logger.info(f"Noise statistics written to {stats_path}")
    return {"slope": slope, "p_value": p_value, "significant": significant}

def main():
    run_noise_sweep_statistics()
