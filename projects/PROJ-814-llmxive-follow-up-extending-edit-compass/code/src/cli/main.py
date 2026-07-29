import argparse
import sys
import logging
from pathlib import Path

from src.utils.logging import get_logger, setup_logging
from src.services.download import main as download_main
from src.services.filter import main as filter_main

logger = get_logger(__name__)


def run_download_filter(args):
    """Execute the download and filter pipeline stages sequentially."""
    logger.info("Starting download-filter pipeline")

    # Stage 1: Download
    logger.info("Stage 1: Downloading Edit-Compass dataset")
    try:
        download_main()
    except Exception as e:
        logger.error(f"Download stage failed: {e}")
        sys.exit(1)

    # Stage 2: Filter
    logger.info("Stage 2: Filtering dataset for target categories")
    try:
        filter_main()
    except Exception as e:
        logger.error(f"Filter stage failed: {e}")
        sys.exit(1)

    logger.info("Download-filter pipeline completed successfully")


def run_score(args):
    """Execute the scoring stage."""
    logger.info("Starting scoring pipeline")
    # Placeholder for T021 implementation
    logger.warning("Scoring stage not yet implemented (T021)")
    sys.exit(1)


def run_analyze(args):
    """Execute the analysis stage."""
    logger.info("Starting analysis pipeline")
    # Placeholder for T030 implementation
    logger.warning("Analysis stage not yet implemented (T030)")
    sys.exit(1)


def run_all(args):
    """Execute the full pipeline."""
    logger.info("Starting full pipeline")
    run_download_filter(args)
    run_score(args)
    run_analyze(args)


def main():
    parser = argparse.ArgumentParser(
        description="llmXive Automated Science Pipeline CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Pipeline stages")

    # download-filter stage
    dl_parser = subparsers.add_parser(
        "download-filter",
        help="Download and filter the Edit-Compass dataset"
    )
    dl_parser.set_defaults(func=run_download_filter)

    # score stage
    score_parser = subparsers.add_parser(
        "score",
        help="Compute Logic and Fidelity scores"
    )
    score_parser.set_defaults(func=run_score)

    # analyze stage
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Perform statistical correlation analysis"
    )
    analyze_parser.set_defaults(func=run_analyze)

    # all stage
    all_parser = subparsers.add_parser(
        "all",
        help="Run the complete pipeline"
    )
    all_parser.set_defaults(func=run_all)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    setup_logging()
    args.func(args)


if __name__ == "__main__":
    main()