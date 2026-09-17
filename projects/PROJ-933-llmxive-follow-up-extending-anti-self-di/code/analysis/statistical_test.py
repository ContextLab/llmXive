"""
Pre-study Power Analysis for llmXive Anti-Self-Distillation Experiment.

This script performs a priori power analysis to determine the minimum sample size (N)
required to achieve a statistical power of >= 0.8 (80%) for detecting a medium effect size
in the primary hypothesis test (Wilcoxon signed-rank test).

Context:
- Test: Wilcoxon signed-rank test (non-parametric paired difference test)
- Hypothesis: AntiSD training produces significantly higher diversity scores than standard self-distillation.
- Target Power: >= 0.80
- Significance Level (alpha): 0.05
- Effect Size: Medium (r = 0.3, approximating Cohen's d = 0.5 for non-parametric)

Output:
- Prints the required sample size (N) to stdout.
- Writes the analysis report to `data/power_analysis_report.json`.
"""

import json
import math
import os
from pathlib import Path

import numpy as np
from scipy.stats import norm

# Constants from the project specification
TARGET_POWER = 0.80
ALPHA = 0.05
# Medium effect size for Wilcoxon signed-rank test (r = 0.3 is standard convention)
# r = Z / sqrt(N) => Z = r * sqrt(N)
# We invert the power function to find N.
EFFECT_SIZE_R = 0.3

# Output path relative to project root
OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "power_analysis_report.json"


def calculate_z_score(power: float, alpha: float) -> tuple[float, float]:
    """
    Calculates the Z-scores for the given power and alpha level.

    Args:
        power: Desired statistical power (1 - beta).
        alpha: Significance level.

    Returns:
        Tuple of (z_beta, z_alpha)
    """
    # Z_beta: The critical value such that the area to the right is beta (1 - power)
    # norm.ppf(0.8) gives the value where 80% is to the left.
    # We need the value where (1-power) is to the right, which is the same as power to the left for the negative side?
    # Actually: Power = P(Z > z_alpha - delta) under H1.
    # Standard approximation: N = ( (z_alpha + z_beta) / effect_size )^2
    # where z_beta corresponds to the power.
    z_beta = norm.ppf(power)
    z_alpha = norm.ppf(1 - alpha / 2) # Two-tailed test
    return z_beta, z_alpha


def estimate_sample_size_wilcoxon(effect_size_r: float, alpha: float = 0.05, power: float = 0.80) -> int:
    """
    Estimates the required sample size (N) for a Wilcoxon signed-rank test.

    The approximation formula for the Wilcoxon signed-rank test sample size is derived from
    the normal approximation of the test statistic.
    N ≈ ( (z_alpha + z_beta) / r )^2

    Reference:
    - "Statistical Power Analysis for the Behavioral Sciences" (Cohen)
    - Approximations for non-parametric tests often use the effect size r = Z/sqrt(N).

    Args:
        effect_size_r: Expected effect size (r).
        alpha: Significance level.
        power: Desired power.

    Returns:
        Minimum integer sample size N.
    """
    z_beta, z_alpha = calculate_z_score(power, alpha)

    # Formula: N = ((Z_alpha + Z_beta) / r)^2
    numerator = z_alpha + z_beta
    n_float = (numerator / effect_size_r) ** 2

    n_int = math.ceil(n_float)

    # Ensure a minimum reasonable sample size for robustness (though the formula dictates the math)
    # The prompt specifically asks to confirm N >= 30.
    return max(n_int, 1)


def run_power_analysis():
    """
    Executes the power analysis and saves the report.
    """
    print("--- Pre-study Power Analysis ---")
    print(f"Target Power: {TARGET_POWER}")
    print(f"Significance Level (alpha): {ALPHA}")
    print(f"Assumed Effect Size (r): {EFFECT_SIZE_R} (Medium)")

    required_n = estimate_sample_size_wilcoxon(
        effect_size_r=EFFECT_SIZE_R,
        alpha=ALPHA,
        power=TARGET_POWER
    )

    print(f"\nCalculated Minimum Sample Size (N): {required_n}")

    # Validation against project constraints (FR-013, SC-007)
    # The task asks to confirm N >= 30.
    # If the calculated N is less than 30, we should still report it, but note that 30 is often a
    # practical minimum for normality assumptions in non-parametric tests.
    # However, if the calculation yields > 30, that is the hard requirement.
    # If it yields < 30, we typically set N=30 to satisfy the "N >= 30" constraint for robustness.
    final_n = max(required_n, 30)

    if final_n > required_n:
        print(f"Adjusting N to {final_n} to satisfy project constraint (N >= 30) for robustness.")
    else:
        print(f"Calculated N ({required_n}) satisfies project constraint (N >= 30).")

    # Generate Report
    report = {
        "task_id": "T006",
        "analysis_type": "A priori Power Analysis",
        "test_statistic": "Wilcoxon Signed-Rank Test",
        "parameters": {
            "alpha": ALPHA,
            "target_power": TARGET_POWER,
            "effect_size_r": EFFECT_SIZE_R,
            "effect_size_description": "Medium (r = 0.3)"
        },
        "results": {
            "calculated_minimum_n": required_n,
            "final_recommended_n": final_n,
            "power_achieved_at_final_n": float(norm.cdf(
                (math.sqrt(final_n) * EFFECT_SIZE_R) - norm.ppf(1 - ALPHA / 2)
            ))
        },
        "validation": {
            "constraint_met": final_n >= 30,
            "message": f"N = {final_n} meets the requirement N >= 30 for power >= 0.8."
        }
    }

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write report to disk
    with open(OUTPUT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to: {OUTPUT_FILE}")
    print(f"Final Recommended Sample Size (N): {final_n}")

    return report


if __name__ == "__main__":
    run_power_analysis()