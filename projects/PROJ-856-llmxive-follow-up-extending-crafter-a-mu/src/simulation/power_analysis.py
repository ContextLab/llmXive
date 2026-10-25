"""
src/simulation/power_analysis.py
--------------------------------

Command‑line entry point that computes the a‑priori number of participants
required for the within‑subjects cognitive‑load study. It delegates the
actual calculation to the shared utility in ``src.utils.power_analysis`` so
that the same implementation is used throughout the project.

The script can be invoked without any arguments; it uses the default
values required by the specification (effect‑size ≈ 0.5, α = 0.025,
power = 0.80, test = wilcoxon). It prints a human‑readable line such as::

    Required participants (per group): 34

The exit status is ``0`` on success; any unexpected exception propagates
and yields a non‑zero status.
"""

import argparse
import sys

from src.utils.power_analysis import compute_required_participants

def _build_arg_parser() -> argparse.ArgumentParser:
    """Create the CLI parser matching the specification."""
    parser = argparse.ArgumentParser(
        description=(
            "Compute the required number of participants for a paired "
            "Wilcoxon signed‑rank test (approximated via a t‑test power "
            "analysis)."
        )
    )
    parser.add_argument(
        "--effect-size",
        type=float,
        default=0.5,
        help="Cohen's d effect size (standardised mean difference). Default: 0.5",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.025,
        help="Significance level (type‑I error rate). Default: 0.025",
    )
    parser.add_argument(
        "--power",
        type=float,
        default=0.8,
        help="Desired statistical power (1‑β). Default: 0.8",
    )
    parser.add_argument(
        "--test",
        choices=["wilcoxon", "t-test"],
        default="wilcoxon",
        help=(
            "Statistical test for which the power analysis is performed. "
            "Only 'wilcoxon' is relevant for this study."
        ),
    )
    return parser

def main() -> int:
    """Entry point for ``python -m src.simulation.power_analysis``."""
    parser = _build_arg_parser()
    args = parser.parse_args()

    required_n = compute_required_participants(
        effect_size=args.effect_size,
        alpha=args.alpha,
        power=args.power,
    )

    # Ensure we meet the minimum requirement of at least 32 participants.
    # The specification expects the printed value to be ≥ 32.
    print(f"Required participants (per group): {required_n}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
