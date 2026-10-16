"""
Power Analysis Module for MobileForge Logic Distillation.

This module implements the a‑priori McNemar power analysis required by
FR‑007. It uses ``statsmodels.stats.power.GofChisquarePower`` to compute the
required sample size (N) for a paired proportion test with the following
fixed parameters:

- Target power: 0.8
- Effect size (Cohen's h): 0.2
- Significance level (α): 0.05
- Baseline success rate (p₀): 0.5 (conservative assumption)

The script aborts if any data‑extraction artifacts already exist
(files under ``data/processed``) to enforce the “before extraction” rule.
The result is written to ``data/validated_n.json`` and conforms to the 
JSON schema at ``contracts/power_analysis.schema.yaml``.
"""

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from statsmodels.stats.power import GofChisquarePower
from llmxive_toolkit import paths

def _ensure_no_extraction_artifacts() -> None:
    """
    Ensure that no data‑extraction artifacts are present. The presence of any
    file inside ``data/processed`` indicates that extraction has already been
    performed, and power analysis must be run **before** that step.
    """
    processed_dir = paths.data("processed")
    if processed_dir.exists() and any(processed_dir.iterdir()):
        raise RuntimeError(
            f"Data‑extraction artifacts already exist in '{processed_dir}'. "
            "Power analysis must be performed before any extraction step."
        )

def calculate_required_n(
    effect_size: float = 0.2,
    alpha: float = 0.05,
    power: float = 0.8,
    baseline_p0: float = 0.5,
) -> Dict[str, Any]:
    """
    Calculate the required sample size (N) using ``GofChisquarePower``.

    Parameters
    ----------
    effect_size : float
        Cohen's h (minimum detectable difference in proportions).
    alpha : float
        Significance level (type‑I error rate).
    power : float
        Desired statistical power (1‑type‑II error rate).
    baseline_p0 : float
        Baseline success rate. Must be 0.5 as per project constraints.

    Returns
    -------
    dict
        Dictionary containing ``n_required`` and a ``parameters`` block.
    """
    # Validate inputs
    if not (0 < effect_size < 1):
        raise ValueError("effect_size must be between 0 and 1.")
    if not (0 < alpha < 1):
        raise ValueError("alpha must be between 0 and 1.")
    if not (0 < power < 1):
        raise ValueError("power must be between 0 and 1.")
    if baseline_p0 != 0.5:
        raise ValueError("baseline_p0 must be 0.5 (conservative assumption).")

    # Use statsmodels to solve for required observations.
    # GofChisquarePower expects Cohen's w (identical to Cohen's h for
    # two‑proportion tests), so we can pass the effect_size directly.
    power_analysis = GofChisquarePower()
    n_required = power_analysis.solve_power(
        effect_size=effect_size,
        nobs=None,
        alpha=alpha,
        power=power,
    )
    # ``solve_power`` may return a float; round up to guarantee the desired power.
    n_required_int = int(math.ceil(n_required))

    result = {
        "n_required": n_required_int,
        "parameters": {
            "power_target": power,
            "effect_size": effect_size,
            "significance_level": alpha,
            "baseline_rate": baseline_p0,
            "p0_source": "Conservative 0.5 assumption",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return result

def main() -> None:
    """
    Entry point for the power‑analysis script.
    """
    print("Running a‑priori power analysis for MobileForge Logic Distillation...")
    try:
        # Enforce the “before extraction” rule.
        _ensure_no_extraction_artifacts()

        # Fixed parameters as dictated by the task specification.
        effect_size = 0.2
        alpha = 0.05
        power = 0.8
        baseline_p0 = 0.5

        result = calculate_required_n(
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            baseline_p0=baseline_p0,
        )
        
        # Write to project-owned data directory (NOT state/)
        output_file = paths.data("validated_n.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, sort_keys=True)

        print("Power analysis completed successfully.")
        print(f"  Required N          : {result['n_required']}")
        print(f"  Effect size (h)    : {result['parameters']['effect_size']}")
        print(f"  Alpha (α)          : {result['parameters']['significance_level']}")
        print(f"  Target power (1‑β) : {result['parameters']['power_target']}")
        print(f"  Baseline p₀        : {result['parameters']['baseline_rate']}")
        print(f"  Output written to  : {output_file}")

    except Exception as exc:
        print(f"Error during power analysis: {exc}")
        raise

if __name__ == "__main__":
    main()