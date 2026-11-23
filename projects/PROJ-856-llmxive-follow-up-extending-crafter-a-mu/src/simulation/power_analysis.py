"""
src/simulation/power_analysis.py
--------------------------------

Command‑line entry point that computes the a‑priori number of participants
required for the within‑subjects cognitive‑load study.
"""

import argparse
import sys

from src.utils.power_analysis import compute_required_participants

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute the required number of participants for a paired Wilcoxon signed‑rank test."
    )
    parser.add_argument("--effect-size", type=float, default=0.5)
    parser.add_argument("--alpha", type=float, default=0.025)
    parser.add_argument("--power", type=float, default=0.8)
    parser.add_argument("--test", choices=["wilcoxon", "t-test"], default="wilcoxon")
    return parser

def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    required_n = compute_required_participants(
        effect_size=args.effect_size,
        alpha=args.alpha,
        power=args.power,
    )

    # Print the result as required by T006 verification
    print(f"Required participants (per group): {required_n}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
