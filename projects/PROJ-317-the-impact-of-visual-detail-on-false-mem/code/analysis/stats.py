"""
Statistical analysis utilities for the Visual Detail and False Memory project.

This module provides functions for power analysis, ANOVA calculations, and
other statistical tests required for the research pipeline.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

from statsmodels.stats.power import FTestAnovaPower


def calculate_power_analysis(
    alpha: float = 0.05,
    power: float = 0.80,
    effect_size: float = 0.25,
    k_groups: int = 3,
) -> Dict[str, Any]:
    """
    Calculate the required sample size for a one-way repeated measures ANOVA.

    Parameters
    ----------
    alpha : float
        Significance level (default: 0.05).
    power : float
        Desired statistical power (default: 0.80).
    effect_size : float
        Cohen's f effect size (default: 0.25 for medium effect).
    k_groups : int
        Number of groups/conditions in the ANOVA (default: 3).

    Returns
    -------
    Dict[str, Any]
        Dictionary containing the analysis parameters and the calculated
        sample size per group.
    """
    solver = FTestAnovaPower()

    # Calculate required sample size (n per group)
    n = solver.solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power,
        k_groups=k_groups,
    )

    # Round up to the nearest integer
    n_rounded = int(n) + (1 if n % 1 > 0 else 0)

    result = {
        "alpha": alpha,
        "power": power,
        "effect_size": effect_size,
        "k_groups": k_groups,
        "sample_size_per_group": n_rounded,
        "total_sample_size": n_rounded * k_groups,
        "notes": (
            f"Calculated for one-way repeated measures ANOVA with "
            f"{k_groups} conditions. Assumes medium effect size (Cohen's f={effect_size})."
        ),
    }

    return result


def save_power_analysis(result: Dict[str, Any], output_path: str) -> None:
    """
    Save the power analysis results to a JSON file.

    Parameters
    ----------
    result : Dict[str, Any]
        The power analysis result dictionary.
    output_path : str
        Path to the output JSON file.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)


def main() -> None:
    """
    Main entry point for running the power analysis.

    Calculates the required sample size and saves the result to
    data/processed/power_analysis.json.
    """
    # Define output path relative to project root
    # Assuming this script is run from the project root or code/analysis/
    project_root = Path(__file__).resolve().parents[2]
    output_path = project_root / "data" / "processed" / "power_analysis.json"

    # Run power analysis with default parameters
    result = calculate_power_analysis(
        alpha=0.05,
        power=0.80,
        effect_size=0.25,  # Cohen's f = 0.25 (medium effect)
        k_groups=3,        # Baseline, Enhanced, Reduced conditions
    )

    # Save results
    save_power_analysis(result, str(output_path))

    print(f"Power analysis complete.")
    print(f"  Effect size (Cohen's f): {result['effect_size']}")
    print(f"  Alpha: {result['alpha']}")
    print(f"  Power: {result['power']}")
    print(f"  Groups: {result['k_groups']}")
    print(f"  Sample size per group: {result['sample_size_per_group']}")
    print(f"  Total sample size: {result['total_sample_size']}")
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()
