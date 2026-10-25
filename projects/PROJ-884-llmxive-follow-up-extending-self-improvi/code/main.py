"""
Top‑level entry point for the project.

The original quick‑start script expected ``python -m code.main``.  This module
now forwards the command‑line arguments to the appropriate sub‑module
(currently the BES pilot runner).  Keeping the public interface stable
satisfies the existing ``quickstart.md`` while allowing the BES implementation
to evolve independently.
"""

import argparse
import sys
from pathlib import Path

# The pilot runner lives in ``code.bes.main`` – importing it lazily avoids
# unnecessary heavy imports (e.g. Transformers) when the user only wants the
# pilot mode.
def _run_pilot(args: argparse.Namespace) -> int:
    """Execute the pilot pipeline and return an exit‑code."""
    from code.bes.main import run_pilot
    return run_pilot(seed=args.seed)

def _run_full(args: argparse.Namespace) -> int:
    """Execute the full BES experiment (symbolic‑guided)."""
    from code.bes.main import run_full
    return run_full(
        seed=args.seed,
        generations=args.generations,
        population_size=args.population_size,
    )

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="llmXive BES – pilot and full experiment runner"
    )
    parser.add_argument(
        "--pilot",
        action="store_true",
        help="Run the minimal pilot dataset + verification only",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run the full symbolic‑guided BES loop",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--generations",
        type=int,
        default=10,
        help="Number of generations for the full run",
    )
    parser.add_argument(
        "--population-size",
        type=int,
        default=30,
        help="Population size for the full run",
    )
    args = parser.parse_args(argv)

    if args.pilot and args.full:
        parser.error("Only one of --pilot or --full may be specified")

    if args.pilot:
        return _run_pilot(args)
    elif args.full:
        return _run_full(args)
    else:
        parser.error("Please specify either --pilot or --full")

if __name__ == "__main__":
    sys.exit(main())
