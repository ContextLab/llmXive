"""
Power analysis utility for a within‑subjects design.

This script computes the required number of participants to achieve a
specified statistical power for detecting a given effect size. It is
intended for use with paired designs (e.g., Wilcoxon signed‑rank test).
"""

import argparse
import math
import sys

from statsmodels.stats.power import TTestPower

def compute_required_participants(effect_size: float, alpha: float, power: float) -> int:
    """
    Compute the minimum number of participants for a paired design.

    Parameters
    ----------
    effect_size : float
        Cohen's d (standardized mean difference).
    alpha : float
        Type‑I error rate.
    power : float
        Desired statistical power.

    Returns
    -------
    int
        Ceiling of the required sample size.
    """
    # For a paired design, the required sample size is the same as for a
    # two‑sample t‑test on the differences. TTestPower implements this.
    analysis = TTestPower()
    nobs = analysis.solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power,
        alternative="two-sided",
    )
    # solve_power returns a float; we need the smallest integer >= that value.
    return math.ceil(nobs)

def main() -> int:
    """Entry point for the python -m src.utils.power_analysis command."""
    parser = argparse.ArgumentParser(
        description="Compute a priori power analysis for a within‑subjects design."
    )
    parser.add_argument("--effect-size", type=float, required=True)
    parser.add_argument("--alpha", type=float, required=True)
    parser.add_argument("--power", type=float, default=0.80)
    parser.add_argument("--participants", type=int, default=None)
    args = parser.parse_args()

    required_n = compute_required_participants(
        effect_size=args.effect_size,
        alpha=args.alpha,
        power=args.power,
    )

    print(f"Required participants ≥ {required_n}")

    if args.participants is not None and args.participants < required_n:
        print(f"Planned participants ({args.participants}) is less than the required minimum ({required_n}). Aborting.")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
