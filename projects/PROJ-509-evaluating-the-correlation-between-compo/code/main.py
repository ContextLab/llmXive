import os
import sys
import argparse
from pathlib import Path

from config import load_paths
from utils.logging import setup_logging, get_logger

logger = get_logger(__name__)


def main() -> None:
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Run the materials science pipeline")
    parser.add_argument("--step", type=str, default="all", help="Pipeline step to run")
    args = parser.parse_args()

    paths = load_paths()
    setup_logging(paths)

    logger.info(f"Starting pipeline with step: {args.step}")

    # Placeholder for pipeline orchestration
    if args.step == "all" or args.step == "ingest":
        logger.info("Running ingestion")
        # import subprocess
        # subprocess.run([sys.executable, "code/ingest.py"])

    if args.step == "all" or args.step == "descriptors":
        logger.info("Running descriptor computation")
        # subprocess.run([sys.executable, "code/descriptors.py"])

    if args.step == "all" or args.step == "train":
        logger.info("Running training and evaluation")
        # subprocess.run([sys.executable, "code/evaluate.py"])

    if args.step == "all" or args.step == "importance":
        logger.info("Running feature importance")
        # subprocess.run([sys.executable, "code/importance.py"])

    logger.info("Pipeline complete")


if __name__ == "__main__":
    main()
