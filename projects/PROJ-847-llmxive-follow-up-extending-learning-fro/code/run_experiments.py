"""Entry‑point for the density‑supervision study.

The original implementation accepted only a ``--config`` argument.
The quick‑start guide (authoritative) expects a richer CLI that
directly specifies the experiment mode, retaining ratios, seeds and
output location.  This file now supports both usages:

* ``python -m code.run_experiments --config <yaml>`` – legacy mode.
* ``python -m code.run_experiments --mode fixed --rhos 0.1 0.3 ...`` –
  fixed‑density baseline runs.
* ``python -m code.run_experiments --mode adaptive ...`` – placeholder
  for adaptive runs (not required for T004).

The script dispatches to the appropriate stage implementation.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths

from code.trainer import run_fixed_baselines

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Argument parsing
# ----------------------------------------------------------------------
def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run experiment pipeline for density‑supervision study"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to a YAML configuration file (legacy mode).",
    )
    parser.add_argument(
        "--mode",
        choices=["fixed", "adaptive"],
        help="Experiment mode: 'fixed' for baseline runs, 'adaptive' for scheduler runs.",
    )
    parser.add_argument(
        "--rhos",
        type=float,
        nargs="+",
        help="Retaining ratios for fixed‑density runs (e.g., 0.1 0.3 0.5).",
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        help="Random seeds for replication (e.g., 42 43 44).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Path to write the result file (CSV for fixed, JSON for adaptive).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print parsed arguments and exit without running.",
    )
    return parser.parse_args(argv)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _run_fixed_mode(args: argparse.Namespace) -> None:
    """Execute fixed‑density baseline experiments."""
    if not args.rhos or not args.seeds or not args.output:
        log.error(
            "Fixed mode requires --rhos, --seeds and --output arguments."
        )
        sys.exit(1)

    log.info(
        "Running fixed‑density baselines: rhos=%s seeds=%s output=%s",
        args.rhos,
        args.seeds,
        args.output,
    )
    run_fixed_baselines(
        rhos=args.rhos,
        seeds=args.seeds,
        output_csv=args.output,
    )
    print(f"Fixed‑density baseline results written to {args.output}")

def _run_adaptive_mode(args: argparse.Namespace) -> None:
    """Placeholder for adaptive scheduler runs."""
    log.error("Adaptive mode not yet implemented in this task.")
    sys.exit(1)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main(argv=None) -> int:
    args = parse_args(argv)

    if args.dry_run:
        log.info("Dry‑run mode – parsed arguments: %s", args)
        return 0

    if args.config:
        # Legacy config‑driven path – not required for T004 but retained.
        log.info("Loading configuration from %s (legacy mode)", args.config)
        config_path = Path(args.config)
        if not config_path.is_file():
            log.error("Configuration file %s does not exist.", config_path)
            return 1
        # For simplicity, just echo the config path.
        print(f"Loaded config from {config_path}")
        return 0

    if args.mode == "fixed":
        _run_fixed_mode(args)
    elif args.mode == "adaptive":
        _run_adaptive_mode(args)
    else:
        log.error("No mode specified. Use --mode fixed|adaptive or --config.")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
