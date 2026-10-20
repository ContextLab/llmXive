"""
Orchestration module for the Euler Totient Residue Distribution Analysis.

This module implements the CLI orchestrator required by task T011.
It parses command‑line arguments, pins deterministic seeds, runs the
sieve, statistical analysis, flag generation and visualisation stages,
and records a benchmark JSON for the whole run.

The script can be executed as a module:

    python -m code.run_analysis --N 200 --primes 3 5

All output files are written under the ``data/`` and ``results/``
directories as specified in the project specification.
"""

import sys
import argparse
import logging
import json
from typing import Dict, Any, List

from llmxive_toolkit import get_logger

# Local imports
from config import load_config, create_argument_parser, parse_cli_args
from seed import pin_seeds
from sieve import compute_phi_linear_sieve, compute_residues, save_residue_dataset
from memory_guard import MemoryGuard
from stats import (
    run_full_statistical_analysis,
    save_statistical_result,
)
from flags import generate_flag_from_result
from visualize import (
    load_residue_data,
    plot_bar_frequencies,
    plot_residual_qq,
    annotate_theoretical_bounds,
    generate_visualization_report,
)
from benchmark import benchmark

# ----------------------------------------------------------------------
# Logging setup
# ----------------------------------------------------------------------
logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper: normalise prime argument to a list of ints
# ----------------------------------------------------------------------
def _normalise_primes(arg: Any) -> List[int]:
    """
    Convert the ``--primes`` CLI argument into a list of ints.

    The argparse configuration accepts ``nargs='+'`` which yields a list
    of strings or ints.  This helper guarantees a clean ``List[int]``.
    """
    if arg is None:
        return [3, 5, 7, 11]
    if isinstance(arg, list):
        return [int(p) for p in arg]
    # Fallback – split a comma‑separated string
    return [int(p) for p in str(arg).split(",")]

# ----------------------------------------------------------------------
# CLI parsing
# ----------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    """
    Parse command‑line arguments, apply defaults required by the test
    suite and return a populated ``argparse.Namespace``.
    """
    parser = create_argument_parser()
    args = parser.parse_args()

    # Apply the defaults expected by the unit tests when arguments are omitted.
    if args.N is None:
        args.N = 1_000_000
    if args.primes is None:
        args.primes = [3, 5, 7, 11]
    else:
        args.primes = _normalise_primes(args.primes)

    if args.seed is None:
        args.seed = 42
    if args.memory_limit_mb is None:
        # The test suite expects 6000 MB as the default.
        args.memory_limit_mb = 6_000
    if args.memory_check_interval is None:
        args.memory_check_interval = 10_000

    return args

# ----------------------------------------------------------------------
# Seed pinning
# ----------------------------------------------------------------------
def pin_orchestration_seed(config: Dict[str, Any]) -> None:
    """
    Pin deterministic seeds for the entire pipeline.

    Parameters
    ----------
    config :
        Configuration dictionary containing a ``seed`` entry.
    """
    seed = config.get("seed", 42)
    pin_seeds(seed)
    logger.info(f"Global seeds pinned to {seed}")

# ----------------------------------------------------------------------
# Sieve stage
# ----------------------------------------------------------------------
def run_sieve_stage(config: Dict[str, Any]) -> None:
    """
    Compute φ values, aggregate residues for each prime and write the
    raw JSON artefacts.

    Parameters
    ----------
    config :
        Dictionary containing ``N``, ``primes`` and ``memory_limit_mb``.
    """
    N = config["N"]
    primes: List[int] = config["primes"]
    memory_limit_mb = config["memory_limit_mb"]

    logger.info(f"Starting sieve stage for N={N}, primes={primes}")

    # Initialise the memory guard – it will be polled inside the sieve.
    guard = MemoryGuard(limit_mb=memory_limit_mb,
                        check_interval=config.get("memory_check_interval", 10_000))

    # Compute φ once – the same list can be reused for all primes.
    phi_vals = compute_phi_linear_sieve(N, memory_guard=guard)

    for prime in primes:
        logger.info(f"Processing prime {prime}")
        residues = compute_residues(phi_vals, prime)
        out_path = f"data/raw/residues_{prime}_{N}.json"
        save_residue_dataset(residues, prime, N, out_path)
        logger.info(f"Residue dataset written to {out_path}")

# ----------------------------------------------------------------------
# Statistics stage
# ----------------------------------------------------------------------
def run_stats_stage(config: Dict[str, Any]) -> None:
    """
    Load each raw residue file, run the full statistical pipeline and
    write the results JSON.  Afterwards a flag file is generated.

    Parameters
    ----------
    config :
        Dictionary containing ``N`` and ``primes``.
    """
    N = config["N"]
    primes: List[int] = config["primes"]
    seed = config.get("seed", 42)

    logger.info("Starting statistics stage")

    for prime in primes:
        raw_path = f"data/raw/residues_{prime}_{N}.json"
        result_path = f"data/processed/stats_{prime}_{N}.json"

        # Load the raw residue JSON – keys are strings, convert to int.
        with open(raw_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        freq_map_raw = raw.get("frequency_map", {})
        observed_counts = {int(k): int(v) for k, v in freq_map_raw.items()}

        # Run the high‑level statistical analysis.
        result = run_full_statistical_analysis(
            observed_counts,
            prime,
            N,
            config={"seed": seed},
        )
        save_statistical_result(result, result_path)
        logger.info(f"Statistical result written to {result_path}")

        # Generate the pass/fail flag JSON.
        generate_flag_from_result(result_path)

# ----------------------------------------------------------------------
# Visualisation stage
# ----------------------------------------------------------------------
def run_visualization_stage(config: Dict[str, Any]) -> None:
    """
    Produce bar‑plots, QQ‑plots and a short markdown report for each prime.

    Parameters
    ----------
    config :
        Dictionary containing ``N`` and ``primes``.
    """
    N = config["N"]
    primes: List[int] = config["primes"]

    logger.info("Starting visualisation stage")

    for prime in primes:
        residue_path = f"data/raw/residues_{prime}_{N}.json"
        stats_path = f"data/processed/stats_{prime}_{N}.json"

        # Load the residue dataset (handles string‑to‑int conversion).
        data = load_residue_data(residue_path)

        # Create the two required figures.
        plot_bar_frequencies(data, prime)
        plot_residual_qq(data, prime)

        # Future‑proof hook – currently a no‑op.
        annotate_theoretical_bounds(prime, data)

        # Write a tiny markdown summary linking the artefacts.
        generate_visualization_report(prime, N, stats_path)

# ----------------------------------------------------------------------
# Orchestration entry point
# ----------------------------------------------------------------------
def run_orchestration(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the full pipeline while measuring wall‑clock time and peak
    memory usage via the ``benchmark`` context manager.

    Returns a dictionary summarising the run (primarily for internal
    debugging; the CLI only cares about the exit code).
    """
    summary: Dict[str, Any] = {"status": "success", "errors": []}

    try:
        with benchmark("fullrun"):
            run_sieve_stage(config)
            run_stats_stage(config)
            run_visualization_stage(config)
    except Exception as exc:
        logger.exception("Pipeline failed")
        summary["status"] = "failed"
        summary["errors"].append(str(exc))

    return summary

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    """
    Parse CLI arguments, load the configuration, pin seeds and run the
    orchestrated pipeline.  Returns ``0`` on success and ``1`` on failure.
    """
    args = parse_args()
    config = load_config(args)

    # Pin deterministic seeds as early as possible.
    pin_orchestration_seed(config)

    result = run_orchestration(config)

    return 0 if result.get("status") == "success" else 1

if __name__ == "__main__":
    sys.exit(main())