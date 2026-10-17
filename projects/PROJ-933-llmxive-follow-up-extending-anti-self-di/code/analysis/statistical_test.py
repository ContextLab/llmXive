"""
Pre‑study Power Analysis for llmXive Anti‑Self‑Distillation Experiment.

This script determines the minimum sample size (N) required to achieve a
statistical power of at least 0.8 for a Wilcoxon signed‑rank test, given a
medium effect size d = 0.5 and a significance level α = 0.05.

The resulting JSON report is written to:
    results/pre_study_power.json

The report includes:
  - calculated_minimum_n
  - final_recommended_n (enforced N ≥ 30)
  - power_achieved_at_final_n
  - all input parameters for reproducibility
"""

import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import norm

# ----------------------------------------------------------------------
# Configuration (matches the specification)
# ----------------------------------------------------------------------
TARGET_POWER = 0.80          # Desired power (1 - β)
ALPHA = 0.05                 # Significance level
EFFECT_SIZE_D = 0.5          # Medium effect size (Cohen's d)

# Convert Cohen's d to the effect size r used in the normal approximation:
# r = d / sqrt(2)  (for paired tests)
EFFECT_SIZE_R = EFFECT_SIZE_D / math.sqrt(2)  # ≈ 0.3535

# Output location (project‑wide results directory)
OUTPUT_PATH = Path("results") / "pre_study_power.json"


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def calculate_z_scores(power: float, alpha: float) -> tuple[float, float]:
    """
    Compute the Z‑scores for the desired power (β) and significance level (α).

    Returns:
        (z_beta, z_alpha) where:
          - z_beta = Φ⁻¹(power)
          - z_alpha = Φ⁻¹(1 - α/2)   # two‑tailed test
    """
    z_beta = norm.ppf(power)                 # Φ⁻¹(power)
    z_alpha = norm.ppf(1 - alpha / 2)        # two‑tailed critical value
    return z_beta, z_alpha

def estimate_sample_size_wilcoxon(effect_size_r: float,
                                  alpha: float = 0.05,
                                  power: float = 0.80) -> int:
    """
    Approximate the required sample size N for a Wilcoxon signed‑rank test
    using the normal approximation:

        N ≈ ((z_α + z_β) / r)²

    Args:
        effect_size_r: Expected effect size r.
        alpha: Significance level.
        power: Desired statistical power.

    Returns:
        Minimum integer N.
    """
    z_beta, z_alpha = calculate_z_scores(power, alpha)
    n_float = ((z_alpha + z_beta) / effect_size_r) ** 2
    return math.ceil(n_float)

def achieved_power(sample_n: int,
                  effect_size_r: float,
                  alpha: float = 0.05) -> float:
    """
    Compute the statistical power achieved for a given sample size N.

    The formula inverts the normal approximation:
        power = Φ(z_α - r * √N)

    Returns:
        Power (between 0 and 1).
    """
    z_alpha = norm.ppf(1 - alpha / 2)  # two‑tailed
    non_central_param = effect_size_r * math.sqrt(sample_n)
    # Power = 1 - Φ(z_α - δ)  where δ = r * √N
    power = 1 - norm.cdf(z_alpha - non_central_param)
    return power


# ----------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------
def run_power_analysis() -> dict:
    """
    Execute the power analysis, enforce the project constraint N ≥ 30,
    write a JSON report, and return the report dictionary.
    """
    print("--- Pre‑study Power Analysis ---")
    print(f"Target Power: {TARGET_POWER}")
    print(f"Significance Level (α): {ALPHA}")
    print(f"Assumed Effect Size (d): {EFFECT_SIZE_D} (Medium)")

    # ------------------------------------------------------------------
    # Step 1 – Compute the raw minimum N from the approximation
    # ------------------------------------------------------------------
    raw_n = estimate_sample_size_wilcoxon(
        effect_size_r=EFFECT_SIZE_R,
        alpha=ALPHA,
        power=TARGET_POWER,
    )

    print(f"Calculated Minimum Sample Size (N): {raw_n}")

    # ------------------------------------------------------------------
    # Step 2 – Enforce the project‑wide robustness constraint (N ≥ 30)
    # ------------------------------------------------------------------
    final_n = max(raw_n, 30)
    if final_n > raw_n:
        print(
            f"Adjusting N to {final_n} to satisfy project constraint "
            "(N >= 30) for robustness."
        )
    else:
        print("Calculated N satisfies the N >= 30 constraint.")

    # ------------------------------------------------------------------
    # Step 3 – Compute the achieved power at the final N
    # ------------------------------------------------------------------
    power_at_final = achieved_power(final_n, EFFECT_SIZE_R, ALPHA)
    print(f"Power achieved at N = {final_n}: {power_at_final:.4f}")

    # ------------------------------------------------------------------
    # Step 4 – Assemble the JSON report
    # ------------------------------------------------------------------
    report = {
        "task_id": "T001",
        "analysis_type": "A priori Power Analysis",
        "test_statistic": "Wilcoxon Signed‑Rank Test",
        "parameters": {
            "alpha": ALPHA,
            "target_power": TARGET_POWER,
            "effect_size_d": EFFECT_SIZE_D,
            "effect_size_r": round(EFFECT_SIZE_R, 5),
            "effect_size_description": "Medium (d = 0.5)",
        },
        "results": {
            "calculated_minimum_n": raw_n,
            "final_recommended_n": final_n,
            "power_achieved_at_final_n": float(power_at_final),
        },
        "validation": {
            "constraint_N_ge_30": final_n >= 30,
            "constraint_power_ge_0_8": power_at_final >= TARGET_POWER,
            "message": (
                "Both N >= 30 and power >= 0.8 are satisfied."
                if (final_n >= 30 and power_at_final >= TARGET_POWER)
                else "One or more constraints are not satisfied."
            ),
        },
    }

    # ------------------------------------------------------------------
    # Step 5 – Write the report to disk
    # ------------------------------------------------------------------
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to: {OUTPUT_PATH}")
    print(f"Final recommended sample size (N): {final_n}")
    print(f"Achieved power: {power_at_final:.4f}")

    return report


if __name__ == "__main__":
    run_power_analysis()