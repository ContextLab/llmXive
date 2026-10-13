"""Minimal orchestration script for the three major pipeline stages."""

import argparse
import logging
import sys

from code.data.download import download_hcp_subset
from code.data.preprocess import run_preprocessing_pipeline
from code.data.merge import run_merge_pipeline
from code.features.connectivity import main as connectivity_main

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _run_download_preprocess() -> None:
    """Download raw data and run preprocessing, then merge."""
    logger.info("Downloading raw data (HCP subset)...")
    download_hcp_subset()
    logger.info("Running preprocessing pipeline...")
    processed_count = run_preprocessing_pipeline()
    if processed_count == 0:
        logger.error("Preprocessing failed or produced no subjects.")
        sys.exit(1)
    logger.info(f"Preprocessing completed for {processed_count} subjects.")

    logger.info("Running merge pipeline to create exclusion log...")
    merged_df, success = run_merge_pipeline()
    if not success:
        logger.error("Merge pipeline failed.")
        sys.exit(1)


def _run_features() -> None:
    """Run the connectivity feature extraction stage."""
    logger.info("Running connectivity feature extraction...")
    ret = connectivity_main()
    if ret != 0:
        logger.error("Connectivity pipeline failed.")
        sys.exit(1)
    logger.info("Feature extraction completed.")


def main() -> None:
    """Entry point for the project."""
    parser = argparse.ArgumentParser(description="Project entry point.")
    parser.add_argument(
        "--stage",
        type=str,
        required=True,
        choices=[
            "download_preprocess",
            "features",
            "analysis",
        ],
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
