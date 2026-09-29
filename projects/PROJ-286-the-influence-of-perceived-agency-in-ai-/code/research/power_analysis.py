"""
Power analysis calculation for the Perceived Agency study.

Calculates required sample size for:
1. One-way ANOVA (Omnibus test)
2. Planned directional contrasts

Uses scipy and numpy for calculations.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
from scipy import stats


def normalize_contrast(contrast: list) -> list:
    """
    Normalize a contrast vector to unit length.
    
    Args:
        contrast: List of contrast coefficients.
        
    Returns:
        Normalized contrast vector.
    """
    contrast = np.array(contrast, dtype=float)
    norm = np.linalg.norm(contrast)
    if norm == 0:
        raise ValueError("Cannot normalize a zero vector")
    return (contrast / norm).tolist()


def calculate_contrast_power(
    effect_size: float,
    alpha: float,
    n_per_group: int,
    num_groups: int,
    contrast: list
) -> Tuple[float, float]:
    """
    Calculate power for a planned contrast.
    
    For a contrast with k groups, the non-centrality parameter is:
    lambda = n * f^2 * (sum(c_i^2) / k)
    where c_i are the contrast coefficients (normalized).
    
    Args:
        effect_size: Cohen's f effect size.
        alpha: Significance level.
        n_per_group: Number of participants per group.
        num_groups: Number of groups (3 for this study).
        contrast: Contrast coefficients.
        
    Returns:
        Tuple of (power, critical_f_value).
    """
    # Normalize the contrast
    norm_contrast = normalize_contrast(contrast)
    
    # Calculate the non-centrality parameter (lambda)
    # For a contrast: lambda = n * f^2 * sum(c_i^2) where c_i are normalized
    # Since we normalized, sum(c_i^2) = 1
    # But we need to account for the number of groups
    lambda_ncp = n_per_group * (effect_size ** 2) * num_groups
    
    # Degrees of freedom for the contrast (always 1)
    df1 = 1
    df2 = num_groups * (n_per_group - 1)
    
    # Critical F value
    critical_f = stats.f.ppf(1 - alpha, df1, df2)
    
    # Power = P(F > critical_f | H1)
    # Using non-central F distribution
    power = 1 - stats.ncf.cdf(critical_f, df1, df2, lambda_ncp)
    
    return float(power), float(critical_f)


def calculate_anova_power(
    effect_size: float,
    alpha: float,
    n_per_group: int,
    num_groups: int
) -> Tuple[float, float]:
    """
    Calculate power for one-way ANOVA (omnibus test).
    
    Args:
        effect_size: Cohen's f effect size.
        alpha: Significance level.
        n_per_group: Number of participants per group.
        num_groups: Number of groups.
        
    Returns:
        Tuple of (power, critical_f_value).
    """
    # Non-centrality parameter for ANOVA
    # lambda = n * k * f^2
    lambda_ncp = n_per_group * num_groups * (effect_size ** 2)
    
    # Degrees of freedom
    df1 = num_groups - 1
    df2 = num_groups * (n_per_group - 1)
    
    # Critical F value
    critical_f = stats.f.ppf(1 - alpha, df1, df2)
    
    # Power = P(F > critical_f | H1)
    power = 1 - stats.ncf.cdf(critical_f, df1, df2, lambda_ncp)
    
    return float(power), float(critical_f)


def find_minimum_n(
    target_power: float,
    effect_size: float,
    alpha: float,
    num_groups: int,
    contrast: Optional[list] = None,
    max_n: int = 500
) -> int:
    """
    Find the minimum n per group to achieve target power.
    
    Args:
        target_power: Desired power level.
        effect_size: Cohen's f effect size.
        alpha: Significance level.
        num_groups: Number of groups.
        contrast: Optional contrast vector for contrast power calculation.
        max_n: Maximum n to search.
        
    Returns:
        Minimum n per group.
    """
    for n in range(2, max_n + 1):
        if contrast is not None:
            power, _ = calculate_contrast_power(
                effect_size, alpha, n, num_groups, contrast
            )
        else:
            power, _ = calculate_anova_power(
                effect_size, alpha, n, num_groups
            )
        
        if power >= target_power:
            return n
    
    raise ValueError(f"Could not achieve target power {target_power} within n={max_n}")


def main():
    """Main execution for power analysis."""
    # Design parameters (hard-coded as per task specification)
    effect_size = 0.25  # Medium effect size (Cohen's f)
    alpha = 0.05
    target_power = 0.80
    num_groups = 3  # High, Low, Control

    # Planned contrasts (orthogonal)
    # Contrast 1: High vs Low [1, -1, 0]
    # Contrast 2: (High + Low) vs Control [0.5, 0.5, -1]
    contrasts = {
        "high_vs_low": [1, -1, 0],
        "combined_vs_control": [0.5, 0.5, -1]
    }

    # Calculate minimum n for ANOVA
    n_anova = find_minimum_n(
        target_power, effect_size, alpha, num_groups, contrast=None
    )

    # Calculate minimum n for each contrast
    contrast_n_results = {}
    for name, contrast in contrasts.items():
        n_contrast = find_minimum_n(
            target_power, effect_size, alpha, num_groups, contrast=contrast
        )
        contrast_n_results[name] = n_contrast

    # The final sample size is the maximum of all requirements
    final_n = max(n_anova, max(contrast_n_results.values()))

    # Calculate actual power at final_n for all tests
    anova_power, anova_critical_f = calculate_anova_power(
        effect_size, alpha, final_n, num_groups
    )

    contrast_powers = {}
    for name, contrast in contrasts.items():
        power, critical_f = calculate_contrast_power(
            effect_size, alpha, final_n, num_groups, contrast
        )
        contrast_powers[name] = {
            "power": power,
            "critical_f": critical_f,
            "n_per_group": final_n
        }

    # Prepare results
    results = {
        "params": {
            "effect_size": effect_size,
            "alpha": alpha,
            "target_power": target_power,
            "num_groups": num_groups,
            "contrasts": {
                name: {
                    "coefficients": contrast,
                    "description": "High vs Low" if name == "high_vs_low" else "Combined vs Control"
                }
                for name, contrast in contrasts.items()
            }
        },
        "results": {
            "anova": {
                "n_per_group": n_anova,
                "power_at_final_n": anova_power,
                "critical_f": anova_critical_f
            },
            "contrasts": contrast_powers,
            "final_n": final_n,
            "total_sample_size": final_n * num_groups
        }
    }

    # Ensure output directory exists
    output_path = Path("research/power_calculation.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write results
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Power analysis complete. Results written to {output_path}")
    print(f"Required sample size: {final_n} per group ({final_n * num_groups} total)")
    print(f"ANOVA power at this size: {anova_power:.4f}")
    for name, res in contrast_powers.items():
        print(f"  {name} power: {res['power']:.4f}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Power analysis for Perceived Agency study")
    parser.add_argument("--effect-size", type=float, default=0.25, help="Cohen's f effect size")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level")
    parser.add_argument("--power", type=float, default=0.80, help="Target power")
    parser.add_argument("--output", type=str, default="research/power_calculation.json", help="Output file path")
    args = parser.parse_args()

    # Override defaults if provided
    if args.effect_size:
        main.__globals__['effect_size'] = args.effect_size
    if args.alpha:
        main.__globals__['alpha'] = args.alpha
    if args.power:
        main.__globals__['target_power'] = args.power

    main()
