"""
Power analysis calculation for the Perceived Agency in AI Interactions study.

Calculates required sample sizes for:
1. Planned directional contrasts (High vs. Low, Combined vs. Control)
2. Overall One-Way ANOVA design

Uses hardcoded design parameters: effect_size=0.25, alpha=0.05, power=0.80
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
from scipy.stats import ncf, f

# Hardcoded design parameters
EFFECT_SIZE = 0.25  # Medium effect size (f)
ALPHA = 0.05
POWER_TARGET = 0.80
N_GROUPS = 3  # High, Low, Control

# Contrast coefficients
# Contrast 1: High vs. Low -> [-1, 1, 0]
# Contrast 2: (High+Low) vs. Control -> [1, 1, -2]
CONTRAST_1 = np.array([-1, 1, 0])
CONTRAST_2 = np.array([1, 1, -2])

def normalize_contrast(contrast: np.ndarray) -> np.ndarray:
    """Normalize contrast vector to unit length."""
    return contrast / np.linalg.norm(contrast)

def calculate_contrast_power(
    effect_size: float,
    alpha: float,
    power_target: float,
    n_groups: int = 3,
    contrast: Optional[np.ndarray] = None
) -> int:
    """
    Calculate required sample size per group for a specific contrast.
    
    Args:
        effect_size: Cohen's f effect size
        alpha: Significance level
        power_target: Target statistical power
        n_groups: Number of groups in the design
        contrast: Contrast vector (defaults to High vs. Low)
    
    Returns:
        Required sample size per group to achieve target power
    """
    if contrast is None:
        contrast = CONTRAST_1
    
    contrast = normalize_contrast(contrast)
    
    for n_per_group in range(10, 10000):
        N = n_per_group * n_groups
        
        # Non-centrality parameter for the contrast
        # lambda = N * f^2 * sum(c_i^2)
        lambda_val = N * (effect_size ** 2) * np.sum(contrast ** 2)
        
        df1 = 1  # Contrast has 1 degree of freedom
        df2 = N - n_groups
        
        # Calculate power using non-central F distribution
        critical_f = f.ppf(1 - alpha, df1, df2)
        power = 1 - ncf.cdf(critical_f, df1, df2, lambda_val)
        
        if power >= power_target:
            return n_per_group
    
    return None

def calculate_anova_power(
    effect_size: float,
    alpha: float,
    power_target: float,
    n_groups: int = 3
) -> int:
    """
    Calculate required sample size per group for overall One-Way ANOVA.
    
    Args:
        effect_size: Cohen's f effect size
        alpha: Significance level
        power_target: Target statistical power
        n_groups: Number of groups in the design
    
    Returns:
        Required sample size per group to achieve target power
    """
    for n_per_group in range(10, 10000):
        N = n_per_group * n_groups
        
        # Non-centrality parameter for ANOVA
        # lambda = N * f^2
        lambda_val = N * (effect_size ** 2)
        
        df1 = n_groups - 1
        df2 = N - n_groups
        
        # Calculate power using non-central F distribution
        critical_f = f.ppf(1 - alpha, df1, df2)
        power = 1 - ncf.cdf(critical_f, df1, df2, lambda_val)
        
        if power >= power_target:
            return n_per_group
    
    return None

def main():
    """Execute power analysis and write results to research/power_calculation.json."""
    # Ensure research directory exists
    research_dir = Path("research")
    research_dir.mkdir(exist_ok=True)
    
    output_path = research_dir / "power_calculation.json"
    
    print(f"Running power analysis with parameters:")
    print(f"  Effect size (f): {EFFECT_SIZE}")
    print(f"  Alpha: {ALPHA}")
    print(f"  Target power: {POWER_TARGET}")
    print(f"  Number of groups: {N_GROUPS}")
    print()
    
    # Calculate for Contrast 1: High vs. Low
    print("Calculating power for Contrast 1: High vs. Low...")
    n_contrast_1 = calculate_contrast_power(
        EFFECT_SIZE, ALPHA, POWER_TARGET, N_GROUPS, CONTRAST_1
    )
    print(f"  Required N per group: {n_contrast_1}")
    
    # Calculate for Contrast 2: (High+Low) vs. Control
    print("Calculating power for Contrast 2: (High+Low) vs. Control...")
    n_contrast_2 = calculate_contrast_power(
        EFFECT_SIZE, ALPHA, POWER_TARGET, N_GROUPS, CONTRAST_2
    )
    print(f"  Required N per group: {n_contrast_2}")
    
    # Calculate for overall ANOVA
    print("Calculating power for overall One-Way ANOVA...")
    n_anova = calculate_anova_power(EFFECT_SIZE, ALPHA, POWER_TARGET, N_GROUPS)
    print(f"  Required N per group: {n_anova}")
    
    # Determine final N (maximum of all calculations)
    n_contrast = max(n_contrast_1, n_contrast_2)
    final_n = max(n_contrast, n_anova)
    
    print()
    print(f"Final recommended sample size per group: {final_n}")
    print(f"Total sample size (N): {final_n * N_GROUPS}")
    
    # Prepare output structure
    output_data: Dict[str, Any] = {
        "params": {
            "effect_size": EFFECT_SIZE,
            "alpha": ALPHA,
            "power": POWER_TARGET,
            "n_groups": N_GROUPS,
            "contrast_type": "directional_and_anova"
        },
        "results": {
            "calculated_n_contrast_1": n_contrast_1,
            "calculated_n_contrast_2": n_contrast_2,
            "calculated_n_contrast": n_contrast,
            "calculated_n_anova": n_anova,
            "final_n": final_n,
            "total_n": final_n * N_GROUPS,
            "contrast_1_coefficients": CONTRAST_1.tolist(),
            "contrast_2_coefficients": CONTRAST_2.tolist()
        }
    }
    
    # Write to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\nResults written to: {output_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
