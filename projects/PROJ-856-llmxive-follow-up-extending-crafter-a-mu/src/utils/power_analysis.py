"""
Power analysis utility for a within‑subjects design.

This script computes the required number of participants to achieve a
specified statistical power for detecting a given effect size. It is
intended for use with paired designs (e.g., Wilcoxon signed‑rank test).
The script prints a human‑readable message of the form:

    Required participants ≥ <N>

If the optional ``--participants`` argument is supplied and the planned
number of participants is smaller than the required minimum, the script
exits with a non‑zero status code to abort the pipeline.
"""

import argparse
import math
import sys

from statsmodels.stats.power import TTestPower

def _build_arg_parser() -> argparse.ArgumentParser:
    """Create the command‑line argument parser."""
    parser = argparse.ArgumentParser(
        description="Compute a priori power analysis for a within‑subjects design."
    )
    parser.add_argument(
        "--effect-size",
        type=float,
        required=True,
        help="Cohen's d effect size (medium ≈ 0.5).",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        required=True,
        help="Significance level (e.g., 0.05).",
    )
    parser.add_argument(
        "--power",
        type=float,
        default=0.80,
        help="Desired statistical power (default: 0.80).",
    )
    parser.add_argument(
        "--test",
        type=str,
        default="wilcoxon",
        choices=["wilcoxon", "t-test"],
        help="Statistical test to be used (informational only).",
    )
    parser.add_argument(
        "--participants",
        type=int,
        default=None,
        help=(
            "Planned number of participants. If provided and less than the "
            "required minimum, the script will exit with status 1."
        ),
    )
    return parser

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
    # two‑sample t‑test on the differences. ``TTestPower`` implements this.
    analysis = TTestPower()
    nobs = analysis.solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power,
        alternative="two-sided",
    )
    # ``solve_power`` returns a float; we need the smallest integer ≥ that value.
    required_n = math.ceil(nobs)
    return required_n

def main() -> int:
    """Entry point for the ``python -m src.utils.power_analysis`` command."""
    parser = _build_arg_parser()
    args = parser.parse_args()

    required_n = compute_required_participants(
        effect_size=args.effect_size,
        alpha=args.alpha,
        power=args.power,
    )

    print(f"Required participants ≥ {required_n}")

    if args.participants is not None:
        if args.participants < required_n:
            print(
                f"Planned participants ({args.participants}) "
                f"is less than the required minimum ({required_n}). "
                "Aborting."
            )
            return 1  # Non‑zero exit code signals failure.

    return 0

if __name__ == "__main__":
    sys.exit(main())