"""
Statistical analysis module: Regression and hypothesis testing.
"""
import csv
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from scipy import stats

def apply_bonferroni_correction(p_values: List[float], n_tests: int) -> List[float]:
    """Apply Bonferroni correction to a list of p-values."""
    corrected = [p * n_tests for p in p_values]
    return [min(p, 1.0) for p in corrected]

def run_noise_regression(root: Path) -> None:
    """
    Perform linear regression on noise sweep data.
    Outputs data/processed/noise_stats.csv.
    """
    logger = logging.getLogger("statistics")
    logger.info("Running Noise Regression...")

    input_path = root / "data" / "processed" / "noise_sweep_data.csv"
    output_path = root / "data" / "processed" / "noise_stats.csv"

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    # Read data
    data = []
    with open(input_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)

    # Group by sigma
    sigmas = sorted(list(set(float(row['sigma']) for row in data)))
    results = []

    p_values = []

    for sigma in sigmas:
        subset = [row for row in data if float(row['sigma']) == sigma]
        biases = [float(row['bias']) for row in subset]
        gt_e = float(subset[0]['ground_truth_ellipticity']) # Assuming constant GT for this sigma group? No, varies.
        
        # We need to regress Bias vs Sigma? Or Bias vs something else?
        # The task says: "linking artifact magnitude to parameter deviation"
        # Artifact magnitude = sigma. Deviation = bias.
        # We perform a t-test or regression across the whole dataset?
        # The spec says: "Linear Regression on the data... linking artifact magnitude to parameter deviation"
        # Let's do a simple linear fit: Bias = slope * sigma + intercept
        # But we need to aggregate per sigma to get mean bias first?
        # The output schema has: sigma, mean_bias, p_value, significant, slope, intercept.
        # This implies we might be doing a regression per sigma? Or one global regression?
        # Given the output schema, it looks like one row per sigma level with stats about that level.
        # But slope/intercept suggests a global model.
        
        # Interpretation: Calculate mean bias for this sigma.
        # Perform a t-test against 0?
        # And maybe a global regression for slope/intercept?
        
        mean_bias = np.mean(biases)
        
        # T-test against 0
        t_stat, p_val = stats.ttest_1samp(biases, 0.0)
        p_values.append(p_val)

        results.append({
            "sigma": sigma,
            "mean_bias": mean_bias,
            "p_value": p_val,
            "significant": p_val < 0.05,
            "slope": 0.0, # Placeholder for global
            "intercept": 0.0
        })

    # Global regression for slope/intercept
    all_sigmas = [float(row['sigma']) for row in data]
    all_biases = [float(row['bias']) for row in data]
    
    if len(all_sigmas) > 1:
        slope, intercept, r_value, p_val_global, std_err = stats.linregress(all_sigmas, all_biases)
    else:
        slope, intercept = 0.0, 0.0

    # Update results with global slope/intercept
    for r in results:
        r['slope'] = slope
        r['intercept'] = intercept

    # Write output
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["sigma", "mean_bias", "p_value", "significant", "slope", "intercept"])
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Noise regression complete. Results saved to {output_path}")

def run_saturation_regression(root: Path) -> None:
    """
    Perform linear regression on saturation sweep data.
    Outputs data/processed/saturation_stats.csv.
    """
    logger = logging.getLogger("statistics")
    logger.info("Running Saturation Regression...")

    input_path = root / "data" / "processed" / "saturation_sweep.csv"
    output_path = root / "data" / "processed" / "saturation_stats.csv"

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    data = []
    with open(input_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['valid'] == 'True':
                data.append(row)

    fractions = sorted(list(set(float(row['saturation_fraction']) for row in data)))
    results = []
    p_values = []

    for frac in fractions:
        subset = [row for row in data if float(row['saturation_fraction']) == frac]
        biases = [float(row['bias_mean']) for row in subset]
        
        if len(biases) == 0:
            continue

        mean_bias = np.mean(biases)
        t_stat, p_val = stats.ttest_1samp(biases, 0.0)
        p_values.append(p_val)

        results.append({
            "saturation_fraction": frac,
            "mean_bias": mean_bias,
            "p_value": p_val,
            "significant": p_val < 0.05,
            "slope": 0.0,
            "intercept": 0.0
        })

    # Global regression
    all_fracs = [float(row['saturation_fraction']) for row in data]
    all_biases = [float(row['bias_mean']) for row in data]

    if len(all_fracs) > 1:
        slope, intercept, r_value, p_val_global, std_err = stats.linregress(all_fracs, all_biases)
    else:
        slope, intercept = 0.0, 0.0

    for r in results:
        r['slope'] = slope
        r['intercept'] = intercept

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["saturation_fraction", "mean_bias", "p_value", "significant", "slope", "intercept"])
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Saturation regression complete. Results saved to {output_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=str, required=True)
    args = parser.parse_args()
    root = Path(args.root)
    run_noise_regression(root)
    run_saturation_regression(root)

if __name__ == "__main__":
    main()
