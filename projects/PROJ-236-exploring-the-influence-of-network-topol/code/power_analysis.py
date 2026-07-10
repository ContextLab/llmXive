"""
Statistical Power Analysis for Correlation Detection.

This script calculates the required sample size (N) to detect a correlation
coefficient of at least r=0.3 with a statistical power of >= 0.80,
using a two-tailed test at alpha=0.05.

It uses the `statsmodels` library to perform the calculation based on
the non-central t-distribution approximation for Pearson correlation.

Output:
    Prints the required sample size N to stdout.
    Writes the result to `data/analysis/power_analysis_result.json` for downstream consumption.
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm
from statsmodels.stats.power import tt_solve_power, zt_ind_solve_power

# Ensure the data/analysis directory exists
OUTPUT_DIR = Path("data/analysis")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def calculate_sample_size_for_correlation(
    effect_size: float = 0.3,
    alpha: float = 0.05,
    power: float = 0.80,
    alternative: str = "two-sided"
) -> int:
    """
    Calculate the minimum sample size required to detect a correlation.

    Since statsmodels does not have a direct 'correlation' power function
    that returns N directly in older versions without manual transformation,
    we use the Fisher's z-transformation approach which is standard for
    correlation power analysis.

    Fisher's z = 0.5 * ln((1+r)/(1-r))
    Standard error of z = 1 / sqrt(N - 3)

    We test H0: rho = 0 vs H1: rho != 0.
    Under H0, z ~ N(0, 1/sqrt(N-3)).
    Under H1, z ~ N(z_rho, 1/sqrt(N-3)).

    The required N is derived from:
    N = ( (Z_{1-alpha/2} + Z_{power}) / z_rho )^2 + 3

    Where:
    - Z_{1-alpha/2} is the critical value for the significance level.
    - Z_{power} is the critical value for the desired power.
    - z_rho is the Fisher transformed effect size.
    """
    if effect_size == 0:
        raise ValueError("Effect size (correlation) cannot be zero for this calculation.")

    # Fisher Z-transformation of the effect size
    # Clamp to [-0.999, 0.999] to avoid log(0) or log(inf)
    r_clamped = np.clip(effect_size, -0.999, 0.999)
    z_rho = 0.5 * np.log((1 + r_clamped) / (1 - r_clamped))

    # Critical values
    if alternative == "two-sided":
        z_alpha = norm.ppf(1 - alpha / 2)
    else:
        z_alpha = norm.ppf(1 - alpha)

    z_beta = norm.ppf(power)

    # Calculate N
    # N - 3 = ((z_alpha + z_beta) / z_rho)^2
    n_minus_3 = ((z_alpha + z_beta) / z_rho) ** 2
    n = n_minus_3 + 3

    # Round up to the nearest integer
    return int(np.ceil(n))

def main():
    """
    Main entry point for the power analysis script.
    """
    print("Starting Power Analysis for Correlation Detection...")
    print(f"Target Correlation (r): 0.3")
    print(f"Target Power: 0.80")
    print(f"Significance Level (alpha): 0.05")

    try:
        required_n = calculate_sample_size_for_correlation(
            effect_size=0.3,
            alpha=0.05,
            power=0.80,
            alternative="two-sided"
        )

        result = {
            "effect_size_r": 0.3,
            "target_power": 0.80,
            "alpha": 0.05,
            "required_sample_size_N": required_n,
            "methodology": "Fisher's z-transformation approximation"
        }

        # Print result to stdout
        print(f"\nResult: A sample size of N = {required_n} is required.")
        print(f"Calculated N (float): {required_n - 3 + 3:.2f} (raw calculation)")

        # Save to file
        output_path = OUTPUT_DIR / "power_analysis_result.json"
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        print(f"Result saved to: {output_path}")

        # Return code 0 on success
        return 0

    except Exception as e:
        print(f"Error during power analysis: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
