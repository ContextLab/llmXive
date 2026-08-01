"""
Separability Analysis Module for llmXive.

This module implements statistical power analysis and separability checks
for latent space disentanglement between text and image modalities.
"""

import json
import os
from pathlib import Path

import numpy as np
from scipy.stats import ttest_ind, norm

# Constants for Power Analysis
# Target power (1 - beta)
TARGET_POWER = 0.80
# Significance level (alpha)
ALPHA = 0.05
# Minimum detectable effect size (Cohen's d) as per task requirement
MIN_EFFECT_SIZE = 0.8

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"


def calculate_sample_size_for_power(effect_size: float = MIN_EFFECT_SIZE,
                                    power: float = TARGET_POWER,
                                    alpha: float = ALPHA) -> int:
    """
    Calculate the minimum sample size (N per group) required to detect
    a given effect size with specified power and significance level.

    Uses the standard formula for a two-sample t-test (assuming equal variance
    and equal sample sizes).

    Formula: N = 2 * ((Z_alpha/2 + Z_beta) / effect_size)^2

    Args:
        effect_size: Cohen's d (standardized mean difference).
        power: Desired statistical power (1 - beta).
        alpha: Significance level (Type I error rate).

    Returns:
        int: Minimum sample size per group, rounded up.
    """
    # Critical Z value for alpha (two-tailed)
    z_alpha = norm.ppf(1 - alpha / 2)
    # Critical Z value for power (beta)
    z_beta = norm.ppf(power)

    # Calculate N per group
    # N = 2 * ( (Z_alpha + Z_beta) / d )^2
    numerator = z_alpha + z_beta
    n_per_group = 2 * (numerator / effect_size) ** 2

    # Round up to ensure power is met
    return int(np.ceil(n_per_group))


def run_power_analysis(output_path: Path | None = None) -> dict:
    """
    Executes the power analysis calculation and saves results to JSON.

    Args:
        output_path: Path to save the results JSON. Defaults to
                     data/results/power_analysis.json.

    Returns:
        dict: The calculated power analysis metrics.
    """
    if output_path is None:
        output_path = DATA_RESULTS_DIR / "power_analysis.json"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Calculate N required per group
    n_per_group = calculate_sample_size_for_power(
        effect_size=MIN_EFFECT_SIZE,
        power=TARGET_POWER,
        alpha=ALPHA
    )

    # Total N required (two groups: text and image)
    n_total = n_per_group * 2

    # N for manual audit (typically a smaller subset, e.g., 50 or 100)
    # Based on standard audit practices, we'll set a reasonable fixed audit size
    # or scale it if N is extremely large. Let's cap it at 200 for manual feasibility.
    n_audit = min(n_per_group, 200)

    results = {
        "N_required": n_total,
        "N_per_group": n_per_group,
        "effect_size": MIN_EFFECT_SIZE,
        "power": TARGET_POWER,
        "alpha": ALPHA,
        "N_audit": n_audit,
        "description": f"Minimum total samples required to detect effect size {MIN_EFFECT_SIZE} with {TARGET_POWER} power."
    }

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


def main():
    """Main entry point for the power analysis script."""
    print("Starting Power Analysis (Task 0.1)...")
    results = run_power_analysis()
    print(f"Power Analysis Complete.")
    print(f"  Required N (Total): {results['N_required']}")
    print(f"  Required N (Per Group): {results['N_per_group']}")
    print(f"  Audit Sample Size: {results['N_audit']}")
    print(f"  Output saved to: {DATA_RESULTS_DIR / 'power_analysis.json'}")


if __name__ == "__main__":
    main()
