"""
Statistical analysis for bias trends.
"""
import csv
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from scipy import stats
from code.config import RANDOM_SEED

def apply_bonferroni_correction(p_values: List[float], n_tests: int) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    """
    return [min(p * n_tests, 1.0) for p in p_values]

def run_noise_regression(input_csv: Path, output_csv: Path) -> None:
    """
    Perform linear regression on noise sweep data.
    Output: data/processed/noise_stats.csv
    """
    input_csv = Path(input_csv)
    output_csv = Path(output_csv)
    
    # Read data
    data = []
    with open(input_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    # Group by sigma
    sigma_groups: Dict[float, List[float]] = {}
    for row in data:
        sigma = float(row['sigma'])
        bias = float(row['bias'])
        if sigma not in sigma_groups:
            sigma_groups[sigma] = []
        sigma_groups[sigma].append(bias)
    
    # Perform regression: sigma (X) vs mean_bias (Y)
    sigmas = sorted(sigma_groups.keys())
    mean_biases = [np.mean(sigma_groups[s]) for s in sigmas]
    
    # Linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(sigmas, mean_biases)
    
    # Bonferroni correction (n_tests = number of sigma levels)
    n_tests = len(sigmas)
    corrected_p = min(p_value * n_tests, 1.0)
    significant = corrected_p < 0.05
    
    # Write output
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["sigma", "mean_bias", "p_value", "significant", "slope", "intercept"])
        for s, mb in zip(sigmas, mean_biases):
            # We only have one regression line, so we write the same slope/intercept for all
            # But we can write the p-value for the overall fit
            writer.writerow([s, mb, corrected_p, significant, slope, intercept])
    
    logging.info(f"Noise regression stats written to {output_csv}")

def run_saturation_regression(input_csv: Path, output_csv: Path) -> None:
    """
    Perform linear regression on saturation sweep data.
    Output: data/processed/saturation_stats.csv
    """
    input_csv = Path(input_csv)
    output_csv = Path(output_csv)
    
    # Read data
    data = []
    with open(input_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    # Group by saturation_fraction
    sat_groups: Dict[float, List[float]] = {}
    for row in data:
        sat = float(row['saturation_fraction'])
        bias = float(row['bias'])
        if sat not in sat_groups:
            sat_groups[sat] = []
        sat_groups[sat].append(bias)
    
    # Perform regression
    sats = sorted(sat_groups.keys())
    mean_biases = [np.mean(sat_groups[s]) for s in sats]
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(sats, mean_biases)
    
    n_tests = len(sats)
    corrected_p = min(p_value * n_tests, 1.0)
    significant = corrected_p < 0.05
    
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["saturation_fraction", "mean_bias", "p_value", "significant", "slope", "intercept"])
        for s, mb in zip(sats, mean_biases):
            writer.writerow([s, mb, corrected_p, significant, slope, intercept])
    
    logging.info(f"Saturation regression stats written to {output_csv}")

def main():
    root = Path(__file__).resolve().parent.parent.parent
    run_noise_regression(root / "data" / "processed" / "noise_sweep_data.csv",
                         root / "data" / "processed" / "noise_stats.csv")
    run_saturation_regression(root / "data" / "processed" / "saturation_sweep.csv",
                              root / "data" / "processed" / "saturation_stats.csv")

if __name__ == "__main__":
    main()
