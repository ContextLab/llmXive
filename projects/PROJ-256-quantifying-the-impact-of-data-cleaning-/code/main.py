"""
Top‑level pipeline orchestrator.
Provides a CLI that respects configuration values and runs the requested stage(s).
Updated to load configuration from `code/config.py` and pass paths explicitly
to downstream functions, ensuring correct path resolution.
"""
import argparse
import logging
from pathlib import Path
import sys

import pandas as pd
import numpy as np

from config import get_config, reload_config
from utils import setup_logging, pin_random_seed
from data_loader import ensure_data_exists
from analysis import run_baseline_analysis

# Initialise a module‑level logger using the flexible setup_logging utility.
logger = setup_logging(log_level="INFO")


def run_stage_baseline(config) -> None:
    """
    Execute the baseline analysis stage:
    - Ensure raw data exists (downloaded if necessary).
    - Determine input and output locations from the configuration.
    - Invoke ``run_baseline_analysis`` which is tolerant of being passed either
      a raw directory + output path or a pre‑loaded DataFrame.
    - Persist the returned metrics JSON if the analysis function does not
      already write it.
    """
    raw_dir = Path(config.get("RAW_DATA_PATH", "data/raw"))
    processed_dir = Path(config.get("PROCESSED_DATA_PATH", "data/processed"))
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Ensure we have raw data available; this will download the Iris dataset
    # via OpenML if the directory is empty.
    ensure_data_exists()

    # Output location for baseline metrics
    output_file = processed_dir / "baseline_metrics.json"

    # ``run_baseline_analysis`` can accept either a DataFrame or a raw_dir.
    # We delegate the loading to the analysis module for consistency.
    logger.info("Running baseline analysis...")
    result = run_baseline_analysis(
        raw_dir=str(raw_dir),
        output_file=str(output_file)
    )

    # ``run_baseline_analysis`` may already have written the file.
    # If it returns a dict, we ensure the JSON is persisted.
    if isinstance(result, dict):
        output_file.write_text(pd.io.json.dumps(result, indent=2))
        logger.info(f"Baseline metrics written to {output_file}")


def run_stage_cleaning_bootstrap(config) -> None:
    """
    Placeholder for the cleaning + bootstrap stage.
    The full implementation resides in other modules; this function simply
    logs that the stage was requested. In a complete pipeline this would
    invoke the cleaning pipeline, re‑run analysis on each cleaned variant,
    and perform bootstrap variance estimation.
    """
    logger.info("Cleaning + bootstrap stage requested – not fully implemented in this task.")


def run_pipeline(stage: str) -> None:
    """
    Dispatch to the appropriate stage handler based on the CLI argument.
    """
    config = get_config()

    if stage == "baseline":
        run_stage_baseline(config)
    elif stage == "cleaning_bootstrap":
        run_stage_cleaning_bootstrap(config)
    else:
        logger.error(
            f"Unknown stage '{stage}'. Available stages: baseline, cleaning_bootstrap"
        )
        raise SystemExit(1)


def main() -> None:
    """
    CLI entry point.
    Usage:
        python -m code.main [--stage STAGE]
    If no stage is provided, defaults to 'baseline'.
    """
    parser = argparse.ArgumentParser(
        description="Quantifying Data Cleaning Impact Pipeline"
    )
    parser.add_argument(
        "--stage",
        type=str,
        default="baseline",
        help="Pipeline stage to execute (baseline, cleaning_bootstrap)",
    )
    args = parser.parse_args()

    # Ensure deterministic behaviour across runs
    config = get_config()
    pin_random_seed(config.get("RANDOM_SEED", 42))

    try:
        run_pipeline(args.stage)
    except Exception as exc:
        logger.exception(f"Pipeline failed: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
