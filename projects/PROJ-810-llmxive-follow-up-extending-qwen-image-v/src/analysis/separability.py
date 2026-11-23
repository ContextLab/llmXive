import json
import os
from pathlib import Path
import numpy as np
from scipy.stats import ttest_ind, norm

def calculate_sample_size_for_power(effect_size: float = 0.8, power: float = 0.8, alpha: float = 0.05) -> int:
    """
    Calculate the minimum sample size N required to achieve a specified statistical power
    for a two-sample t-test, given an expected effect size (Cohen's d).

    Uses the approximation formula for sample size in a two-sided independent t-test:
    N_per_group = 2 * ((Z_alpha/2 + Z_beta) / effect_size)^2

    Args:
        effect_size: Expected Cohen's d (default 0.8, strictly > 0.8 as per task requirement).
        power: Desired statistical power (1 - beta), default 0.8.
        alpha: Significance level (Type I error), default 0.05.

    Returns:
        Total sample size N (sum of both groups).
    """
    if effect_size <= 0:
        raise ValueError("Effect size must be positive.")
    if not (0 < power < 1):
        raise ValueError("Power must be between 0 and 1.")
    if not (0 < alpha < 1):
        raise ValueError("Alpha must be between 0 and 1.")

    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)

    n_per_group = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    return int(np.ceil(n_per_group * 2))

def run_power_analysis(
    output_path: str = "data/results/power_analysis.json",
    effect_size: float = 0.81,
    power: float = 0.8,
    alpha: float = 0.05
) -> dict:
    """
    Performs power analysis calculation and writes the result to a JSON file.

    Args:
        output_path: Path to write the JSON output.
        effect_size: Effect size (Cohen's d). Must be > 0.8 per task spec.
        power: Target power.
        alpha: Significance level.

    Returns:
        Dictionary containing the analysis results.
    """
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Calculate N
    n_required = calculate_sample_size_for_power(effect_size, power, alpha)

    # Define N_audit as a fraction of N (e.g., 5% or minimum 10) for manual audit
    n_audit = max(10, int(np.ceil(n_required * 0.05)))

    result = {
        "N_required": n_required,
        "effect_size": effect_size,
        "power": power,
        "alpha": alpha,
        "N_audit": n_audit
    }

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    return result

def main():
    """Entry point for running power analysis."""
    # Task requirement: effect_size d > 0.8. We use 0.81 to satisfy strictly greater.
    result = run_power_analysis(
        output_path="data/results/power_analysis.json",
        effect_size=0.81,
        power=0.8,
        alpha=0.05
    )
    print(f"Power analysis complete. Results written to data/results/power_analysis.json")
    print(f"Required N: {result['N_required']}, Audit N: {result['N_audit']}")
    return result

if __name__ == "__main__":
    main()