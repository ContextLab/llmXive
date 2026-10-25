"""
src/simulation/power_analysis.py
--------------------------------

Command‑line entry point that computes the a‑priori number of participants
required for the within‑subjects cognitive‑load study. It delegates the
actual calculation to the shared utility in ``src.utils.power_analysis`` so
that the same implementation is used throughout the project.

The script is invoked as::

    python -m src.simulation.power_analysis \\
        --effect-size 0.5 \\
        --alpha 0.025 \\
        --test wilcoxon

and prints a human‑readable line such as::

    Required participants (per group): 34

The exit status is ``0`` on success; any unexpected exception propagates
and yields a non‑zero status.
"""

import argparse
import sys

from src.utils.power_analysis import compute_required_participants

def _build_arg_parser() -> argparse.ArgumentParser:
    """Create the CLI parser matching the utility script."""
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
        required=True,
        help="Cohen's d effect size (standardised mean difference).",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level (type‑I error rate). Default: 0.05.",
    )
    parser.add_argument(
        "--power",
        type=float,
        default=0.8,
        help="Desired statistical power (1‑β). Default: 0.8.",
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

    # The requirement from the specification is that the printed N be
    # at least 30 participants; we simply report the computed value.
    print(f"Required participants (per group): {required_n}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
