"""
Power analysis script for determining the required sample size (N) to detect
a Pearson correlation of a given effect size with a specified statistical power.

The script implements the Fisher Z‑transformation based formula and writes
two output artifacts:

1. ``data/analysis/power_analysis_result.json`` – a JSON file containing the
   full calculation details.
2. ``code/power_analysis_output.txt`` – a plain‑text file containing only the
   integer sample size N.

The module provides a reusable ``calculate_sample_size_for_correlation`` function
and a ``main`` entry point used by the CLI and the test suite.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

# ----------------------------------------------------------------------
# Core calculation
# ----------------------------------------------------------------------
def calculate_sample_size_for_correlation(
    effect_size: float = 0.3,
    alpha: float = 0.05,
    power: float = 0.80,
    alternative: str = "two-sided",
) -> int:
    """
    Calculate the minimum sample size required to detect a Pearson correlation.

    Parameters
    ----------
    effect_size : float
        Target Pearson correlation coefficient (absolute value, e.g., 0.3).
    alpha : float
        Significance level (type‑I error rate), default 0.05.
    power : float
        Desired statistical power (1 - type‑II error rate), default 0.80.
    alternative : str
        Either ``"two-sided"`` or ``"one-sided"``. Determines the critical
        value for the significance level.

    Returns
    -------
    int
        The required sample size rounded up to the nearest integer.
    """
    if effect_size == 0:
        raise ValueError("Effect size (correlation) cannot be zero for this calculation.")

    # Clamp to avoid division‑by‑zero in the Fisher transform.
    r_clamped = np.clip(effect_size, -0.999, 0.999)
    z_rho = 0.5 * np.log((1 + r_clamped) / (1 - r_clamped))

    if alternative == "two-sided":
        z_alpha = norm.ppf(1 - alpha / 2)
    else:
        z_alpha = norm.ppf(1 - alpha)

    z_beta = norm.ppf(power)

    n_minus_3 = ((z_alpha + z_beta) / z_rho) ** 2
    n = n_minus_3 + 3

    return int(np.ceil(n))

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> int:
    """
    Execute the power analysis with default parameters, write the results
    to the expected output locations, and exit with a status code.

    Returns
    -------
    int
        Exit code (0 = success, non‑zero = failure).
    """
    try:
        # Perform the calculation using the default parameters defined in the
        # specification (effect size r = 0.3, power = 0.80, alpha = 0.05).
        required_n = calculate_sample_size_for_correlation()

        # ------------------------------------------------------------------
        # 1. Write JSON result (used by other verification tests)
        # ------------------------------------------------------------------
        result = {
            "effect_size_r": 0.3,
            "target_power": 0.8,
            "alpha": 0.05,
            "required_sample_size_N": required_n,
            "methodology": "Fisher's z-transformation approximation",
        }

        json_path = Path("data/analysis/power_analysis_result.json")
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

        # ------------------------------------------------------------------
        # 2. Persist the integer sample size to the required text file
        # ------------------------------------------------------------------
        txt_path = Path("code/power_analysis_output.txt")
        txt_path.write_text(str(required_n), encoding="utf-8")

        # Successful execution
        return 0
    except Exception as exc:  # pragma: no cover – any unexpected error should be visible
        print(f"[ERROR] Power analysis failed: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
