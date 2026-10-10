"""
Orchestrator script for the llmXive follow‑up EvoPolicyGym extension.

Provides three primary CLI flags:
  --check               Verify that required pre‑condition files exist.
  --run-evolution       Execute the evolutionary harness pipeline.
  --run-full-pipeline   Run the complete downstream pipeline:
                        1) Generate dynamic‑shift environment wrappers.
                        2) Run shift sensitivity analysis.
                        3) Run shift validation (p‑value calculation).
                        4) Run the evolutionary harness.
                        5) Run statistical analysis.

Optional arguments:
  --seeds SEEDS [SEEDS ...]         List of random seeds (default: [42]).
  --runs RUNS                       Number of runs per seed (default: 5).
  --conditions CONDITION [CONDITION ...]
                                    Conditions to evaluate (default: baseline counterfactual).

The script exits with status 0 on success and non‑zero on any error.
"""

import argparse
import sys
import os
import json
import logging

# Ensure the project root is on the import path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logging import setup_logging, get_logger
from utils.config import get_config
from envs.dynamic_shift_env import generate_all_dynamic_shift_envs
from analysis.run_shift_sensitivity import main as run_shift_analysis_main
from analysis.shift_validation import main as run_shift_validation_main
from analysis.stats import main as run_stats_analysis_main
from agents.evolutionary_harness import EvolutionaryHarness

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_json(filepath: str):
    """Load a JSON file, raising a clear error if it does not exist."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Required file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def _verify_preconditions():
    """Check that the two mandatory input files exist."""
    missing = []
    for path in ["data/discovered_envs.json", "data/sensitivity_report.csv"]:
        if not os.path.exists(path):
            missing.append(path)
    if missing:
        raise FileNotFoundError(
            f"Pre‑condition check failed – missing file(s): {', '.join(missing)}"
        )
    logger.info("All pre‑conditions satisfied")

# ----------------------------------------------------------------------
# CLI command implementations
# ----------------------------------------------------------------------
def cmd_check(_args):
    """Implementation of the --check flag."""
    try:
        _verify_preconditions()
        print("All pre‑conditions satisfied")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

def cmd_run_evolution(args):
    """Implementation of the --run-evolution flag."""
    # Verify that the sensitivity report exists before proceeding
    if not os.path.exists("data/sensitivity_report.csv"):
        logger.error("Missing data/sensitivity_report.csv – run shift analysis first.")
        sys.exit(1)

    # Load discovered environment IDs
    try:
        env_ids = _load_json("data/discovered_envs.json")
    except Exception as e:
        logger.error(f"Failed to load discovered environments: {e}")
        sys.exit(1)

    # Resolve optional arguments
    config = get_config()
    seeds = args.seeds if args.seeds else config.get("seeds", [42])
    runs = args.runs if args.runs else config.get("runs", 5)
    conditions = (
        args.conditions
        if args.conditions
        else config.get("conditions", ["baseline", "counterfactual"])
    )

    logger.info(
        f"Running Evolutionary Harness with seeds={seeds}, runs={runs}, conditions={conditions}"
    )
    harness = EvolutionaryHarness(
        env_ids=env_ids,
        conditions=conditions,
        seeds=seeds,
        runs_per_seed=runs,
    )
    harness.run()
    logger.info("Evolutionary harness completed successfully")

def cmd_run_full_pipeline(args):
    """Implementation of the --run-full-pipeline flag."""
    # ------------------------------------------------------------------
    # 1. Generate Dynamic‑Shift environment wrappers
    # ------------------------------------------------------------------
    logger.info("Generating Dynamic‑Shift environment wrappers")
    try:
        # The function expects a path to the base registry (the discovered IDs JSON)
        # and an output directory where the generated wrappers will be stored.
        generate_all_dynamic_shift_envs(
            env_registry_path="data/discovered_envs.json",
            output_path=os.path.join("code", "environments", "generated"),
        )
    except Exception as e:
        logger.error(f"Failed to generate dynamic‑shift environments: {e}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 2. Shift Sensitivity Analysis
    # ------------------------------------------------------------------
    try:
        run_shift_analysis_main()
    except Exception as e:
        logger.error(f"Shift sensitivity analysis failed: {e}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 3. Shift Validation (p‑value calculation)
    # ------------------------------------------------------------------
    try:
        run_shift_validation_main()
    except Exception as e:
        logger.error(f"Shift validation failed: {e}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 4. Evolutionary Harness
    # ------------------------------------------------------------------
    # Re‑use the same logic as the --run-evolution command
    cmd_run_evolution(args)

    # ------------------------------------------------------------------
    # 5. Statistical Analysis
    # ------------------------------------------------------------------
    try:
        run_stats_analysis_main()
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        sys.exit(1)

    logger.info("Full pipeline completed successfully")

# ----------------------------------------------------------------------
# Argument parsing
# ----------------------------------------------------------------------
def build_parser():
    parser = argparse.ArgumentParser(
        description="llmXive Follow‑up: EvoPolicyGym Extension Orchestrator"
    )
    # Global optional arguments used by several commands
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        help="Random seeds to use (e.g., --seeds 42 43)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        help="Number of runs per seed (default from config or 5)",
    )
    parser.add_argument(
        "--conditions",
        type=str,
        nargs="+",
        help="Conditions to evaluate (e.g., baseline counterfactual)",
    )

    # Mutually exclusive primary actions
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--check",
        action="store_true",
        help="Verify that required pre‑condition files exist",
    )
    group.add_argument(
        "--run-evolution",
        action="store_true",
        help="Execute the evolutionary harness pipeline",
    )
    group.add_argument(
        "--run-full-pipeline",
        action="store_true",
        help="Run the complete pipeline (shift analysis → validation → evolution → stats)",
    )
    return parser

def main():
    # Initialise logging early so that any errors are captured
    setup_logging(level=logging.INFO)

    parser = build_parser()
    args = parser.parse_args()

    if args.check:
        cmd_check(args)
    elif args.run_evolution:
        cmd_run_evolution(args)
    elif args.run_full_pipeline:
        cmd_run_full_pipeline(args)
    else:
        # This should never happen because argparse enforces one flag
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
