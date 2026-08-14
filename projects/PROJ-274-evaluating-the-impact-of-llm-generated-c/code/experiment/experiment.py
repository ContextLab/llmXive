"""
Experiment Runner for PROJ-274.

This script acts as the primary entry point for the onboarding experiment
as referenced in the run-book (quickstart.md). It delegates to the
data_collection module to manage participant assignment, session logging,
and data export.

Usage:
    python code/experiment/experiment.py --mode mock --participants 3
"""

import argparse
import logging
import sys
import os

# Add the project root to the path to allow imports from sibling modules
# This ensures the script runs correctly regardless of the CWD
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data_collection import (
    main as run_data_collection_main,
    ensure_data_directory,
    assign_participant,
    log_session_start,
    log_session_end,
    export_raw_data
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """
    Entry point for the experiment runner.
    Parses arguments and orchestrates the data collection flow.
    """
    parser = argparse.ArgumentParser(
        description="Run the LLM-generated code documentation onboarding experiment."
    )
    parser.add_argument(
        "--mode",
        choices=["mock", "real"],
        default="mock",
        help="Run mode: 'mock' for simulated participants, 'real' for actual study."
    )
    parser.add_argument(
        "--participants",
        type=int,
        default=0,
        help="Number of participants to simulate (for mock mode)."
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=None,
        help="Repository path or URL (for real mode)."
    )
    parser.add_argument(
        "--commit",
        type=str,
        default=None,
        help="Commit hash to pin (for real mode)."
    )

    args = parser.parse_args()

    logger.info(f"Starting experiment runner in {args.mode} mode.")

    # Ensure data directories exist
    ensure_data_directory()

    if args.mode == "mock":
        logger.info(f"Running mock experiment with {args.participants} participants.")
        if args.participants <= 0:
            logger.error("Mock mode requires --participants > 0")
            sys.exit(1)

        # Run the data collection logic in mock mode
        # We pass the necessary arguments to the underlying main function
        # by simulating the command line args it expects
        mock_args = argparse.Namespace(
            mode="mock",
            participants=args.participants,
            repo=None,
            commit=None,
            output="data/raw/participant_logs.json"
        )
        try:
            run_data_collection_main(mock_args)
        except Exception as e:
            logger.error(f"Mock experiment failed: {e}")
            sys.exit(1)

    elif args.mode == "real":
        logger.info("Running real experiment.")
        if not args.repo:
            logger.error("Real mode requires --repo")
            sys.exit(1)
        
        real_args = argparse.Namespace(
            mode="real",
            participants=0, # Real mode handles assignment internally
            repo=args.repo,
            commit=args.commit,
            output="data/raw/participant_logs.json"
        )
        try:
            run_data_collection_main(real_args)
        except Exception as e:
            logger.error(f"Real experiment failed: {e}")
            sys.exit(1)

    logger.info("Experiment runner completed successfully.")


if __name__ == "__main__":
    main()