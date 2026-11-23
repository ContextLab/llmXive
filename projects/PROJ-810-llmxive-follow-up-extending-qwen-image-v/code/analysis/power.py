"""
Power analysis utility for estimating the minimum sample size required
for a two‑sample t‑test given an effect size, desired power, and significance
level.

This script is invoked via:
    python -m code.analysis.power --output data/results/power_analysis.json

It writes a JSON file containing:
  - N_required: int, required sample size per group
  - effect_size: float, the Cohen's d used for the calculation
  - achieved_power: float, the power achieved with N_required
  - status: "conclusive" if achieved_power >= target power, else "inconclusive"
"""
import argparse
import json
from pathlib import Path

from statsmodels.stats.power import TTestIndPower

# ----------------------------------------------------------------------
# Core functions
# ----------------------------------------------------------------------
def calculate_min_sample_size(effect_size: float, target_power: float, alpha: float) -> int:
    """
    Compute the minimum sample size per group for a two‑sample t‑test.

    Parameters
    ----------
    effect_size : float
        Cohen's d (standardised mean difference).
    target_power : float
        Desired statistical power (e.g., 0.8).
    alpha : float
        Significance level (e.g., 0.05).

    Returns
    -------
    int
        Minimum integer sample size per group.
    """
    solver = TTestIndPower()
    # tt_ind_solve_power returns a float; we round up to the next integer.
    n_float = solver.solve_power(effect_size=effect_size,
                                 power=target_power,
                                 alpha=alpha,
                                 alternative='two-sided')
    # Guard against pathological returns (e.g., None)
    if n_float is None:
        raise RuntimeError("Power analysis failed to compute a sample size.")
    n_int = int(round(n_float))
    if n_int < 2:
        n_int = 2
    return n_int

def run_power_analysis(effect_size: float = 0.8,
                       target_power: float = 0.8,
                       alpha: float = 0.05) -> dict:
    """
    Execute the full power‑analysis pipeline and return a results dictionary.

    Parameters
    ----------
    effect_size : float, default 0.8
    target_power : float, default 0.8
    alpha : float, default 0.05

    Returns
    -------
    dict
        Dictionary with keys:
          - N_required (int)
          - effect_size (float)
          - achieved_power (float)
          - status (str)
    """
    n_required = calculate_min_sample_size(effect_size, target_power, alpha)

    # Compute the actual power achieved with this sample size
    solver = TTestIndPower()
    achieved = solver.power(effect_size=effect_size,
                           nobs1=n_required,
                           alpha=alpha,
                           alternative='two-sided')

    status = "conclusive" if achieved >= target_power else "inconclusive"

    return {
        "N_required": n_required,
        "effect_size": effect_size,
        "achieved_power": round(achieved, 4),
        "status": status
    }

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute minimum sample size for a two‑sample t‑test.")
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to the JSON file where results will be stored.")
    args = parser.parse_args()

    # Run analysis with the specifications from the task description
    results = run_power_analysis(effect_size=0.8,
                                 target_power=0.8,
                                 alpha=0.05)

    # Ensure the output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON results
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
