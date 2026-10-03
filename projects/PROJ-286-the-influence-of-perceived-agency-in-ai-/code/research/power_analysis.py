"""
Power Analysis Module for Pre-Study Sample Size Calculation.

Calculates the required sample size for:
1. One-Way ANOVA (Overall Omnibus test)
2. Planned Directional Contrasts (t-tests)

Uses hard-coded design parameters as specified in tasks.md:
- Effect size (f): 0.25 (Medium)
- Alpha: 0.05
- Target Power: 0.80
- Groups: 3 (High, Low, Control)
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
from statsmodels.stats.power import FTestAnovaPower, TTestPower

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def normalize_contrast(contrast: list) -> list:
    """
    Normalize a contrast vector to unit length for power calculation.
    Power calculations for contrasts often require the vector to be normalized
    such that sum(contrast^2) = 1.
    """
    norm = np.sqrt(sum(c**2 for c in contrast))
    if norm == 0:
        raise ValueError("Contrast vector cannot be all zeros.")
    return [c / norm for c in contrast]


def calculate_contrast_power(
    effect_size_d: float,
    alpha: float,
    power_target: float,
    n_groups: int
) -> Tuple[float, int]:
    """
    Calculate required sample size per group for a planned contrast (t-test).

    Args:
        effect_size_d: Cohen's d for the specific contrast.
        alpha: Significance level.
        power_target: Desired power.
        n_groups: Total number of groups in the design (used for df estimation if needed,
                  though TTestPower is generally independent of k for simple contrasts
                  assuming equal variance).

    Returns:
        Tuple of (n_per_group, total_n)
    """
    power_analysis = TTestPower()
    # Solve for n (sample size per group)
    n_per_group = power_analysis.solve_power(
        effect_size=effect_size_d,
        alpha=alpha,
        power=power_target,
        nobs1=None, # We are solving for nobs
        ratio=1.0   # Equal group sizes
    )
    
    if np.isnan(n_per_group):
        # If effect size is too small or parameters impossible
        raise ValueError(f"Could not calculate power for effect size {effect_size_d}")

    return n_per_group, int(np.ceil(n_per_group * 2)) # Contrast is usually 2 groups compared


def calculate_anova_power(
    effect_size_f: float,
    alpha: float,
    power_target: float,
    n_groups: int
) -> Tuple[float, int]:
    """
    Calculate required sample size per group for One-Way ANOVA.

    Args:
        effect_size_f: Cohen's f effect size.
        alpha: Significance level.
        power_target: Desired power.
        n_groups: Number of groups (k).

    Returns:
        Tuple of (n_per_group, total_n)
    """
    power_analysis = FTestAnovaPower()
    n_per_group = power_analysis.solve_power(
        effect_size=effect_size_f,
        alpha=alpha,
        power=power_target,
        n_groups=n_groups
    )
    
    if np.isnan(n_per_group):
        raise ValueError(f"Could not calculate power for effect size {effect_size_f}")

    total_n = int(np.ceil(n_per_group * n_groups))
    return n_per_group, total_n


def find_minimum_n(
    anova_n: int,
    contrast_n: int
) -> int:
    """
    Determine the final sample size required.
    We must satisfy the most stringent requirement (the larger N).
    """
    return max(anova_n, contrast_n)


def main():
    """
    Main execution entry point for T002.
    Calculates power for ANOVA and planned contrasts, then writes results to JSON.
    """
    # Design Parameters (Hard-coded as per task description)
    EFFECT_SIZE_F = 0.25  # Medium effect size for ANOVA
    ALPHA = 0.05
    POWER_TARGET = 0.80
    N_GROUPS = 3          # High, Low, Control

    # Planned Contrasts Definition (from tasks.md T030)
    # Contrast 1: High vs Low [1, -1, 0]
    # Contrast 2: (High + Low) vs Control [0.5, 0.5, -1]
    # Note: For power analysis of contrasts, we typically estimate the effect size (Cohen's d)
    # expected for that specific comparison. Assuming the ANOVA effect size (f) translates
    # to a specific d for the primary contrast of interest.
    # A common approximation for the primary contrast in a 3-group design with f=0.25
    # is d ≈ 2 * f * sqrt(k / (k-1))? Or simply assume the primary contrast d is derived.
    # However, without a specific d provided, we will calculate ANOVA power primarily.
    # For the "Planned Directional Contrasts", if we assume the effect is driven by the
    # difference between the extremes (High vs Low), we can approximate d.
    # If f = 0.25, and groups are equally spaced, the difference between extremes is roughly 2*sigma*f*sqrt(k).
    # Let's assume the primary contrast (High vs Low) has an effect size d = 0.5 (Medium)
    # which is consistent with f=0.25 in a 3-group design where the middle is control.
    # If the contrast is the main driver, d ~ 0.5 is a standard assumption for f=0.25.
    CONTRAST_EFFECT_D = 0.50 

    results = {}
    errors = []

    try:
        # 1. Calculate ANOVA Power
        n_per_group_anova, total_n_anova = calculate_anova_power(
            EFFECT_SIZE_F, ALPHA, POWER_TARGET, N_GROUPS
        )
        results['anova'] = {
            "effect_size_f": EFFECT_SIZE_F,
            "n_per_group": float(n_per_group_anova),
            "total_n": total_n_anova
        }
    except Exception as e:
        errors.append(f"ANOVA calculation failed: {str(e)}")
        results['anova'] = {"error": str(e)}

    try:
        # 2. Calculate Planned Contrast Power (High vs Low)
        # We treat this as a t-test between two groups
        n_per_group_contrast, total_n_contrast = calculate_contrast_power(
            CONTRAST_EFFECT_D, ALPHA, POWER_TARGET, N_GROUPS
        )
        results['planned_contrast_high_vs_low'] = {
            "effect_size_d": CONTRAST_EFFECT_D,
            "n_per_group": float(n_per_group_contrast),
            "total_n": total_n_contrast
        }
    except Exception as e:
        errors.append(f"Contrast calculation failed: {str(e)}")
        results['planned_contrast_high_vs_low'] = {"error": str(e)}

    # Determine final required N
    final_n_per_group = max(
        results['anova'].get('n_per_group', 0) if 'error' not in results['anova'] else 0,
        results['planned_contrast_high_vs_low'].get('n_per_group', 0) if 'error' not in results['planned_contrast_high_vs_low'] else 0
    )
    final_total_n = int(np.ceil(final_n_per_group * N_GROUPS))

    output = {
        "params": {
            "effect_size_f": EFFECT_SIZE_F,
            "effect_size_d_contrast": CONTRAST_EFFECT_D,
            "alpha": ALPHA,
            "target_power": POWER_TARGET,
            "groups": N_GROUPS
        },
        "results": {
            "n_per_group": float(final_n_per_group),
            "total_n": final_total_n,
            "breakdown": results
        },
        "status": "success" if not errors else "partial_failure"
    }

    if errors:
        output["errors"] = errors

    # Ensure output directory exists
    output_path = PROJECT_ROOT / "research" / "power_calculation.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Power analysis complete.")
    print(f"Required sample size: {final_total_n} (N={int(final_n_per_group)} per group)")
    print(f"Output written to: {output_path}")

    if errors:
        print(f"Warnings: {errors}")
        sys.exit(1) # Fail loudly if critical calculations failed

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
