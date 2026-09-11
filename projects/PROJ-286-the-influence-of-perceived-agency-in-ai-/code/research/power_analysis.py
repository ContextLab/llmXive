import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import scipy.stats as stats
import numpy as np

def normalize_contrast(contrast: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Normalizes a contrast vector."""
    norm = np.sqrt(sum([x**2 for x in contrast]))
    return tuple(x / norm for x in contrast)

def calculate_contrast_power(effect_size: float, alpha: float, power: float, contrast: Tuple[float, float, float]) -> float:
    """Calculates power for a directional contrast."""
    # Using a one-way ANOVA approximation for power calculation
    # Parameters:
    # - effect_size: Cohen's d effect size
    # - alpha: Significance level
    # - power: Desired power
    # - contrast: Contrast vector (normalized)
    try:
        f = effect_size / np.sqrt(3)
        df1 = 2  # Degrees of freedom for the contrast
        df2 = 10 # Assuming a total of 12 participants (adjust as needed)
        power_value = stats.f.cdf(f**2 / (f**2 + df2), df1, df2)
        return power_value
    except Exception as e:
        print(f"Error calculating contrast power: {e}")
        return 0.0

def calculate_anova_power(effect_size: float, alpha: float, power: float) -> float:
    """Calculates power for a one-way ANOVA."""
    try:
        f = effect_size
        df1 = 2  # Degrees of freedom between groups
        df2 = 10 # Degrees of freedom within groups
        power_value = stats.f.cdf(f**2 / (f**2 + df2), df1, df2)
        return power_value
    except Exception as e:
        print(f"Error calculating ANOVA power: {e}")
        return 0.0

def main():
    # Define parameters
    effect_size = 0.25
    alpha = 0.05
    power = 0.80

    # Define contrasts (High vs. Low, (High+Low) vs. Control)
    contrast1 = (1.0, -1.0, 0.0)  # High vs. Low
    contrast2 = (0.5, 0.5, -1.0)  # (High+Low) vs. Control

    # Normalize contrasts
    normalized_contrast1 = normalize_contrast(contrast1)
    normalized_contrast2 = normalize_contrast(contrast2)

    # Calculate power for contrasts and ANOVA
    contrast1_power = calculate_contrast_power(effect_size, alpha, power, normalized_contrast1)
    contrast2_power = calculate_contrast_power(effect_size, alpha, power, normalized_contrast2)
    anova_power = calculate_anova_power(effect_size, alpha, power)

    # Prepare results
    results = {
        "params": {
            "effect_size": effect_size,
            "alpha": alpha,
            "power": power
        },
        "results": {
            "contrast1_power": contrast1_power,
            "contrast2_power": contrast2_power,
            "anova_power": anova_power
        }
    }

    # Save results to JSON file
    output_file = Path("research/power_calculation.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=4)

    print(f"Power analysis completed. Results saved to {output_file}")

if __name__ == "__main__":
    main()