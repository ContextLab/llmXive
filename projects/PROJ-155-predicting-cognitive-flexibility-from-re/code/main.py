"""
Main entry point for the Cognitive Flexibility pipeline.

This script now supports the `--stage` argument used by the quickstart
documentation. The stages are placeholders that log the requested
operation; actual implementations are provided in later tasks.
"""

import argparse
import logging

from code.config import set_seed, get_config
from code.utils.logging import init_logging

logger = logging.getLogger(__name__)

def run_stage(stage: str) -> None:
    """
    Dispatch to the requested pipeline stage.

    Parameters
    ----------
    stage : str
        One of ``download_preprocess``, ``features`` or ``analysis``.
    """
    logger.info(f"Running stage: {stage}")
    # Placeholder implementations – real work will be added in later tasks.
    if stage == "download_preprocess":
        logger.info("Stage 'download_preprocess' selected – no action performed in T001.")
    elif stage == "features":
        logger.info("Stage 'features' selected – no action performed in T001.")
    elif stage == "analysis":
        logger.info("Stage 'analysis' selected – no action performed in T001.")
    else:
        raise ValueError(f"Unknown stage: {stage}")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="llmXive Cognitive Flexibility Pipeline"
    )
    parser.add_argument(
        "--stage",
        choices=["download_preprocess", "features", "analysis"],
        required=True,
        help="Pipeline stage to execute",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable debug logging"
    )
    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    init_logging(log_level)

    # Set random seed
    set_seed(args.seed)

    # Run the requested stage
    run_stage(args.stage)

if __name__ == "__main__":
    main()
