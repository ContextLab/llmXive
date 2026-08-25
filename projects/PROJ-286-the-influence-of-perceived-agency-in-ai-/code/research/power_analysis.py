"""
Power analysis module for calculating required sample sizes for planned directional contrasts.

This module calculates the sample size needed for specific planned contrasts in a
One-Way ANOVA design (High vs. Low, Combined vs. Control) using effect size
transformations for contrasts (f_contrast).
"""
import argparse
import json
import os
import sys
from pathlib import Path
from statsmodels.stats.power import FTestAnovaPower
import numpy as np

def calculate_contrast_effect_size(
    effect_size: float,
    contrast_coeffs: list,
    n_groups: int
) -> float:
    """
    Calculate the effect size (f_contrast) for a specific contrast.

    The contrast effect size is derived from the overall ANOVA effect size (f)
    using the formula: f_contrast = f * sqrt(sum(c_i^2) / k)
    where c_i are the contrast coefficients and k is the number of groups.

    Args:
        effect_size: Overall ANOVA effect size (Cohen's f)
        contrast_coeffs: List of contrast coefficients (sum must be 0)
        n_groups: Number of groups in the design

    Returns:
        Effect size for the specific contrast (f_contrast)
    """
    # Validate contrast coefficients sum to zero
    if abs(sum(contrast_coeffs)) > 1e-6:
        raise ValueError("Contrast coefficients must sum to zero")

    # Validate number of coefficients matches number of groups
    if len(contrast_coeffs) != n_groups:
        raise ValueError(f"Number of coefficients ({len(contrast_coeffs)}) must match number of groups ({n_groups})")

    # Calculate sum of squared coefficients
    sum_sq_coeffs = sum(c**2 for c in contrast_coeffs)

    # Calculate f_contrast
    # Formula: f_contrast = f * sqrt(sum(c_i^2) / k)
    f_contrast = effect_size * np.sqrt(sum_sq_coeffs / n_groups)

    return f_contrast

def calculate_sample_size_for_contrast(
    effect_size: float,
    alpha: float,
    power: float,
    contrast_coeffs: list,
    n_groups: int = 3
) -> int:
    """
    Calculate the required sample size per group for a specific contrast.

    Args:
        effect_size: Overall ANOVA effect size (Cohen's f)
        alpha: Significance level
        power: Target statistical power
        contrast_coeffs: Contrast coefficients
        n_groups: Number of groups (default 3)

    Returns:
        Required sample size per group (rounded up)
    """
    # Calculate contrast-specific effect size
    f_contrast = calculate_contrast_effect_size(
        effect_size=effect_size,
        contrast_coeffs=contrast_coeffs,
        n_groups=n_groups
    )

    # Use statsmodels to calculate sample size
    analysis = FTestAnovaPower()
    n_per_group = analysis.solve_power(
        effect_size=f_contrast,
        alpha=alpha,
        power=power,
        n_groups=n_groups
    )

    if n_per_group is None:
        raise ValueError("Could not calculate sample size. Check input parameters.")

    return int(np.ceil(n_per_group))  # Round up to ensure sufficient power

def main():
    """
    Execute power analysis for planned directional contrasts and save results.

    Calculates sample size for:
    1. High vs. Low contrast: [-1, 1, 0]
    2. Combined (High+Low) vs. Control contrast: [1, 1, -2]

    Uses hardcoded design parameters: effect_size=0.25, alpha=0.05, power=0.80
    """
    # Hardcoded design parameters as per task specification
    effect_size = 0.25  # Medium effect size (Cohen's f)
    alpha = 0.05
    target_power = 0.80
    n_groups = 3  # High, Low, Control

    # Define planned directional contrasts
    contrasts = {
        "high_vs_low": {
            "coefficients": [-1, 1, 0],
            "description": "High Agency vs. Low Agency"
        },
        "combined_vs_control": {
            "coefficients": [1, 1, -2],
            "description": "Combined (High + Low) vs. Control"
        }
    }

    results = {
        "params": {
            "effect_size": effect_size,
            "alpha": alpha,
            "power": target_power,
            "k_groups": n_groups,
            "contrast_type": "planned_directional"
        },
        "results": {}
    }

    # Calculate sample size for each contrast
    max_n_per_group = 0
    for contrast_name, contrast_info in contrasts.items():
        n_per_group = calculate_sample_size_for_contrast(
            effect_size=effect_size,
            alpha=alpha,
            power=target_power,
            contrast_coeffs=contrast_info["coefficients"],
            n_groups=n_groups
        )

        # Calculate contrast-specific effect size for reporting
        f_contrast = calculate_contrast_effect_size(
            effect_size=effect_size,
            contrast_coeffs=contrast_info["coefficients"],
            n_groups=n_groups
        )

        results["results"][contrast_name] = {
            "description": contrast_info["description"],
            "coefficients": contrast_info["coefficients"],
            "f_contrast": round(f_contrast, 4),
            "required_n_per_group": n_per_group,
            "required_total_n": n_per_group * n_groups
        }

        # Track maximum required sample size
        if n_per_group > max_n_per_group:
            max_n_per_group = n_per_group

    # Add summary with maximum required sample size
    results["results"]["summary"] = {
        "max_required_n_per_group": max_n_per_group,
        "max_required_total_n": max_n_per_group * n_groups,
        "recommendation": f"Use {max_n_per_group} participants per group ({max_n_per_group * n_groups} total) to ensure adequate power for all planned contrasts."
    }

    # Ensure output directory exists
    output_dir = Path("research")
    output_dir.mkdir(exist_ok=True)

    # Save results to JSON
    json_path = output_dir / "power_calculation.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Power analysis completed successfully.")
    print(f"Results saved to: {json_path}")
    print(f"\nSummary:")
    for contrast_name, contrast_results in results["results"].items():
        if contrast_name != "summary":
            print(f"  {contrast_results['description']}:")
            print(f"    Coefficients: {contrast_results['coefficients']}")
            print(f"    f_contrast: {contrast_results['f_contrast']}")
            print(f"    Required N per group: {contrast_results['required_n_per_group']}")

    print(f"\nRecommended total sample size: {results['results']['summary']['max_required_total_n']}")
    print(f"  ({results['results']['summary']['max_required_n_per_group']} per group)")

    return results

if __name__ == "__main__":
    main()