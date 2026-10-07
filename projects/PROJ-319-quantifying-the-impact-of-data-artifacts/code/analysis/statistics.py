"""
Statistical analysis: Regression and hypothesis testing.
"""
import csv
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from scipy import stats

try:
    from code.config import get_project_root
except ImportError:
    # Fallback
    import sys
    from pathlib import Path
    parent = Path(__file__).resolve().parent.parent
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))
    from config import get_project_root

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """Apply Bonferroni correction to a list of p-values."""
    n = len(p_values)
    if n == 0:
        return []
    corrected_alpha = alpha / n
    return [p < corrected_alpha for p in p_values]

def run_noise_regression(root: Path):
    """
    Perform linear regression on noise sweep data.
    Output: data/processed/noise_stats.csv
    """
    input_file = root / "data" / "processed" / "noise_sweep_data.csv"
    output_file = root / "data" / "processed" / "noise_stats.csv"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return
    
    # Load data
    data = []
    with open(input_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    # Group by sigma
    sigma_groups = {}
    for row in data:
        sigma = float(row["sigma"])
        if sigma not in sigma_groups:
            sigma_groups[sigma] = []
        sigma_groups[sigma].append(float(row["bias"]))
    
    results = []
    p_values = []
    
    # Simple linear regression: bias ~ sigma
    sigmas = sorted(sigma_groups.keys())
    biases = [np.mean(sigma_groups[s]) for s in sigmas]
    
    if len(sigmas) > 1:
        slope, intercept, r_value, p_val, std_err = stats.linregress(sigmas, biases)
        p_values.append(p_val)
        
        # Bonferroni correction (only one test here, but for generality)
        significant = apply_bonferroni_correction([p_val])[0]
        
        results.append({
            "sigma": sigmas[-1], # Use max sigma for summary or aggregate
            "mean_bias": np.mean(biases),
            "p_value": p_val,
            "significant": significant,
            "slope": slope,
            "intercept": intercept
        })
    else:
        logger.warning("Not enough data points for regression.")
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["sigma", "mean_bias", "p_value", "significant", "slope", "intercept"])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Noise regression stats saved to {output_file}")

def run_saturation_regression(root: Path):
    """
    Perform linear regression on saturation sweep data.
    Output: data/processed/saturation_stats.csv
    """
    input_file = root / "data" / "processed" / "saturation_sweep.csv"
    output_file = root / "data" / "processed" / "saturation_stats.csv"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return
    
    data = []
    with open(input_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    # Group by saturation fraction
    sat_groups = {}
    for row in data:
        frac = float(row["saturation_fraction"])
        if frac not in sat_groups:
            sat_groups[frac] = []
        sat_groups[frac].append(float(row["bias_mean"]))
    
    results = []
    p_values = []
    
    sats = sorted(sat_groups.keys())
    biases = [np.mean(sat_groups[s]) for s in sats]
    
    if len(sats) > 1:
        slope, intercept, r_value, p_val, std_err = stats.linregress(sats, biases)
        p_values.append(p_val)
        
        significant = apply_bonferroni_correction([p_val])[0]
        
        results.append({
            "saturation_fraction": sats[-1],
            "mean_bias": np.mean(biases),
            "p_value": p_val,
            "significant": significant,
            "slope": slope,
            "intercept": intercept
        })
    else:
        logger.warning("Not enough data points for regression.")
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["saturation_fraction", "mean_bias", "p_value", "significant", "slope", "intercept"])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saturation regression stats saved to {output_file}")

def main():
    """Main entry point for statistical analysis."""
    root = get_project_root()
    run_noise_regression(root)
    run_saturation_regression(root)

if __name__ == "__main__":
    main()
