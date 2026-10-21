"""
Power analysis script for the cognitive‑load comparison study.

This module provides a command‑line interface that computes the
minimum required number of participants for a paired within‑subjects
design using the specifications from the project plan.  It relies on
the generic utility implementation in ``src.utils.power_analysis``.
"""

import argparse
import sys

from src.utils.power_analysis import compute_required_participants

def _build_arg_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the power‑analysis CLI."""
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
            "Only 'wilcoxon' is relevant for this study, but the option "
            "is kept for flexibility."
        ),
    )
    return parser

def main() -> int:
    """Entry point for ``python -m src.simulation.power_analysis``."""
    parser = _build_arg_parser()
    args = parser.parse_args()

    # The underlying power‑analysis uses a t‑test approximation, which
    # is acceptable for planning a Wilcoxon signed‑rank test in a
    # within‑subjects design.
    required_n = compute_required_participants(
        effect_size=args.effect_size,
        alpha=args.alpha,
        power=args.power,
    )

    # The result is the total number of participants required (since the
    # design is within‑subjects, each participant experiences both
    # conditions).
    print(f"Required participants (per group): {required_n}")

    # Exit code 0 signals success; any unexpected exception will
    # propagate and cause a non‑zero exit automatically.
    return 0

if __name__ == "__main__":
    sys.exit(main())
