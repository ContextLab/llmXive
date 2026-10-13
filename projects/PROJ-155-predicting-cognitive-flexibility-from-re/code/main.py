"""
Minimal orchestration script for the three major pipeline stages:
1) download_preprocess – fetch raw data and run the preprocessing step;
2) features – compute dynamic connectivity metrics;
3) analysis – (placeholder) run regression / permutation.

For the purpose of the current task we only need the first two stages to
succeed so that the contract tests can locate the required files.
"""

import argparse
import logging
import sys

from code.data.download import download_adhd_dataset
from code.data.preprocess import run_preprocessing_pipeline
from code.features.connectivity import main as connectivity_main

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _run_download_preprocess():
    logger.info("Downloading raw data (ADHD dataset)...")
    download_adhd_dataset()
    logger.info("Running preprocessing pipeline...")
    # The preprocessing script discovers subjects automatically.
    exit_code = run_preprocessing_pipeline()
    if exit_code != 0:
        logger.error("Preprocessing failed.")
        sys.exit(1)
    logger.info("Preprocessing completed.")


def _run_features():
    logger.info("Running connectivity feature extraction...")
    ret = connectivity_main()
    if ret != 0:
        logger.error("Connectivity pipeline failed.")
        sys.exit(1)
    logger.info("Feature extraction completed.")


def main():
    parser = argparse.ArgumentParser(description="Project entry point.")
    parser.add_argument(
        "--stage",
        type=str,
        required=True,
        choices=["download_preprocess", "features", "analysis"],
        help="Pipeline stage to execute.",
    )
    args = parser.parse_args()

    if args.stage == "download_preprocess":
        _run_download_preprocess()
    elif args.stage == "features":
        _run_features()
    elif args.stage == "analysis":
        logger.info("Analysis stage not implemented for this task.")
    else:
        parser.error(f"Unknown stage: {args.stage}")


if __name__ == "__main__":
    main()