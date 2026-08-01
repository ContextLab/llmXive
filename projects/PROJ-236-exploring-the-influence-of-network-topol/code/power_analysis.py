"""
Statistical Power Analysis for Correlation Detection.

This script calculates the required sample size (N) to detect a correlation
coefficient of at least r=0.3 with a statistical power of >= 0.80,
using a two-tailed test at alpha=0.05.

The calculation is based on Fisher's z‑transformation, which is the
standard analytical approximation for correlation power analysis.

Output:
    * Prints the required sample size N to stdout.
    * Writes the result to `data/analysis/power_analysis_result.json` for downstream consumption.
"""

import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

# Ensure the data/analysis directory exists
OUTPUT_DIR = Path("data/analysis")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def calculate_sample_size_for_correlation(
    effect_size: float = 0.3,
    alpha: float = 0.05,
    power: float = 0.80,
    alternative: str = "two-sided",
) -> int:
    """
    Calculate the minimum sample size required to detect a correlation.

    Parameters
    ----------
    effect_size : float
        Target Pearson correlation coefficient (absolute value, e.g., 0.3).
    alpha : float
        Significance level (type‑I error rate), default 0.05.
    power : float
        Desired statistical power (1 - type‑II error rate), default 0.80.
    alternative : str
        Either ``"two-sided"`` or ``"one-sided"``. Determines the critical
        value for the significance level.

    Returns
    -------
    int
        The required sample size rounded up to the nearest integer.

    Notes
    -----
    The formula derives from Fisher's z‑transformation:

        z_r = 0.5 * ln((1+r)/(1-r))

        N = ((z_{1-α/2} + z_{power}) / z_r) ** 2 + 3   (two‑sided)

    where ``z_{1-α/2}`` is the critical normal quantile for the chosen
    significance level and ``z_{power}`` is the normal quantile for the
    desired power.
    """
    if effect_size == 0:
        raise ValueError("Effect size (correlation) cannot be zero for this calculation.")

    # Clamp correlation to avoid log(0) or infinite results
    r_clamped = np.clip(effect_size, -0.999, 0.999)
    z_rho = 0.5 * np.log((1 + r_clamped) / (1 - r_clamped))

    # Critical value for significance level
    if alternative == "two-sided":
        z_alpha = norm.ppf(1 - alpha / 2)
    else:
        z_alpha = norm.ppf(1 - alpha)

    # Critical value for desired power
    z_beta = norm.ppf(power)

    # Compute required N (minus the 3 degrees of freedom correction)
    n_minus_3 = ((z_alpha + z_beta) / z_rho) ** 2
    n = n_minus_3 + 3

    # Round up to the nearest whole number
    return int(np.ceil(n))


def main() -> int:
    """
    Entry point for the power analysis script.
    Returns an exit code (0 for success, 1 for failure).
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
            alternative="two-sided",
        )

        result = {
            "effect_size_r": 0.3,
            "target_power": 0.80,
            "alpha": 0.05,
            "required_sample_size_N": required_n,
            "methodology": "Fisher's z-transformation approximation",
        }

        # Print the result for the user
        print(f"\nResult: A sample size of N = {required_n} is required.")
        # Show the raw (non‑rounded) calculation for transparency
        raw_n = ((norm.ppf(1 - 0.05 / 2) + norm.ppf(0.80)) / (0.5 * np.log((1 + 0.3) / (1 - 0.3)))) ** 2 + 3
        print(f"Calculated N (float, before rounding): {raw_n:.2f}")

        # Persist the result as JSON
        output_path = OUTPUT_DIR / "power_analysis_result.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        print(f"Result saved to: {output_path}")

        return 0

    except Exception as e:  # pragma: no cover – defensive, should not happen
        print(f"Error during power analysis: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
