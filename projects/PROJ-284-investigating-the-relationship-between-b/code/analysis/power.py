import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from typing import Dict, Any, Optional

from config import get_config
from logging_config import get_logger

logger = get_logger(__name__)

def calculate_detectable_effect_size(
    n: int,
    power: float = 0.80,
    alpha: float = 0.05,
    fdr_corrected: bool = True
) -> float:
    """
    Calculate the minimum detectable correlation coefficient (r) for a given sample size.
    Uses the t-distribution approximation for correlation significance.
    
    Args:
        n: Sample size
        power: Desired statistical power (default 0.80)
        alpha: Significance level (default 0.05)
        fdr_corrected: If True, adjust alpha for FDR (conservative estimate)
    
    Returns:
        Minimum detectable r value.
    """
    if n < 3:
        logger.warning("Sample size too small for power analysis")
        return 1.0
    
    # Adjust alpha for FDR if needed (simplified Bonferroni approximation for estimation)
    # In reality, FDR depends on the number of tests, which varies.
    # We assume a conservative adjustment if FDR is requested.
    effective_alpha = alpha
    if fdr_corrected:
        # Assume ~10 tests as a baseline for FDR adjustment estimation
        effective_alpha = alpha / 10.0 
    
    # Degrees of freedom
    df = n - 2
    
    # Critical t-value for the given alpha and power
    # We need the t-value such that P(T > t_crit) = alpha/2 (two-tailed)
    # And the non-centrality parameter corresponding to power.
    # Simplified approach: Use the formula for r from t:
    # t = r * sqrt((n-2) / (1 - r^2))
    # We solve for r given the critical t for alpha and the non-centrality for power.
    
    # Approximation using the inverse of the t-distribution
    # Critical t for significance
    t_crit = stats.t.ppf(1 - effective_alpha / 2, df)
    
    # To achieve power, the non-centrality parameter (delta) must be such that
    # the probability of exceeding t_crit is 'power'.
    # This is complex to solve exactly without non-central t-distribution inversion.
    # We use a standard approximation:
    # r_detectable ~ sqrt( (t_crit^2) / (t_crit^2 + df) ) ... this is for alpha only.
    # For power, we need the effect size that shifts the distribution.
    
    # Standard approximation for minimal detectable r:
    # r = sqrt( (t_alpha + t_beta)^2 / ( (t_alpha + t_beta)^2 + df ) )
    # where t_beta is the t-value for power (1 - beta)
    t_beta = stats.t.ppf(power, df) # This is an approximation for the non-centrality
    
    # More accurate iterative approach or using statsmodels would be ideal,
    # but we stick to scipy/numpy.
    # Let's use the Fisher Z transformation approximation which is more robust.
    # Z_r = 0.5 * ln((1+r)/(1-r))
    # SE = 1 / sqrt(n-3)
    # We need Z_r such that Z_r - 1.96*SE > Z_crit (for alpha)
    # Actually, for power: Z_r > Z_alpha/2 + Z_beta
    
    z_alpha = stats.norm.ppf(1 - effective_alpha / 2)
    z_beta = stats.norm.ppf(power)
    
    # Minimum Z_r required
    z_min = z_alpha + z_beta
    se = 1.0 / np.sqrt(n - 3)
    
    # Required Z_r
    z_r = z_min * se
    
    # Convert back to r
    r = (np.exp(2 * z_r) - 1) / (np.exp(2 * z_r) + 1)
    
    return float(r)

def generate_power_analysis_report(
    correlation_results: pd.DataFrame,
    n_subjects: int,
    output_path: str
) -> None:
    """
    Generate a power analysis report based on achieved sample size and results.
    """
    # Calculate detectable effect size
    detectable_r = calculate_detectable_effect_size(n_subjects)
    
    report = {
        "sample_size": n_subjects,
        "statistical_power": 0.80,
        "alpha": 0.05,
        "fdr_adjusted": True,
        "min_detectable_r": detectable_r,
        "interpretation": f"With N={n_subjects}, the study can detect correlations >= {detectable_r:.3f} with 80% power."
    }
    
    # Save report
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write("# Power Analysis Report\n\n")
        f.write(f"Sample Size: {n_subjects}\n")
        f.write(f"Minimum Detectable r: {detectable_r:.3f}\n")
        f.write(f"Interpretation: {report['interpretation']}\n")
    
    logger.info(f"Power analysis report saved to {output_path}")

def main():
    """
    Main entry point for power analysis.
    """
    setup_logging()
    config = get_config()
    output_dir = config.get("OUTPUT_DIR", "data/analysis")
    
    # This would typically be called after correlations are run
    # For now, we just ensure the function exists and can be imported
    logger.info("Power analysis module ready.")

if __name__ == "__main__":
    main()
