"""
Main orchestrator for the Neural Correlates of Simulated Social Exclusion pipeline.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path

from src.config import load_config
from src.utils import get_logger, setup_logging, log_exception
from src.data_loader import main as run_data_loader
from src.qc import main as run_qc_main
from src.extraction import main as run_extraction_main
from src.connectivity import main as run_connectivity_main
from src.stats import main as run_stats_main
from src.visualization import main as run_visualization_main

logger = get_logger(__name__)

def run_download_qc_step():
    """
    Run data download and QC step.
    Executes data_loader and qc modules.
    """
    logger.info("Starting download_qc step...")
    try:
        logger.info("Running data loader...")
        run_data_loader()
        logger.info("Data loader completed.")
        
        logger.info("Running QC pipeline...")
        run_qc_main()
        logger.info("QC pipeline completed.")
    except Exception as exc:
        log_exception(logger=logger, exc=exc)
        raise

def run_extract_connectivity_step():
    """
    Run extraction and connectivity computation step.
    """
    logger.info("Starting extract_connectivity step...")
    try:
        logger.info("Running extraction pipeline...")
        run_extraction_main()
        logger.info("Extraction pipeline completed.")
        
        logger.info("Running connectivity computation...")
        run_connectivity_main()
        logger.info("Connectivity computation completed.")
    except Exception as exc:
        log_exception(logger=logger, exc=exc)
        raise

def run_stats_viz_step():
    """
    Run statistical analysis and visualization step.
    """
    logger.info("Starting stats_viz step...")
    try:
        logger.info("Running statistical analysis...")
        run_stats_main()
        logger.info("Statistical analysis completed.")
        
        logger.info("Running visualization...")
        run_visualization_main()
        logger.info("Visualization completed.")
    except Exception as exc:
        log_exception(logger=logger, exc=exc)
        raise

def _parse_arguments() -> argparse.Namespace:
    """
    Parse command‑line arguments.

    The original implementation expected a positional ``step`` argument.
    The quick‑start guide, however, uses the ``--step`` flag.  To remain
    backward compatible we accept **both** forms.
    """
    parser = argparse.ArgumentParser(
        description="Run a single step of the neuro‑imaging pipeline."
    )
    # Positional argument (historical)
    parser.add_argument(
        "step_pos",
        nargs="?",
        help="Name of the step to run (positional, legacy).",
    )
    # New ``--step`` flag
    parser.add_argument(
        "--step",
        dest="step_flag",
        help="Name of the step to run (preferred flag).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    return parser.parse_args()

def main() -> int:
    """
    Entry‑point used by the run‑book. Returns an exit‑code compatible
    with the surrounding orchestration.
    """
    args = _parse_arguments()

    # Set up logging
    setup_logging()

    # Resolve which argument the user supplied.
    step = args.step_flag or args.step_pos
    if not step:
        logger.error("Error: no step specified.")
        return 1

    logger.info(f"Running pipeline step: {step}")

    try:
        if step == "download_qc":
            run_download_qc_step()
        elif step == "extract_connectivity":
            run_extract_connectivity_step()
        elif step == "stats_viz":
            run_stats_viz_step()
        else:
            logger.error(f"Unknown step: {step}")
            return 1
    except Exception as exc:
        logger.exception("Pipeline step failed")
        return 1

    logger.info(f"Step {step} completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
