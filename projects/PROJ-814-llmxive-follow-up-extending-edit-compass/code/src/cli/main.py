import argparse
import sys
import logging
from pathlib import Path

# Add project root to path to allow imports from src
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger, setup_logging
from src.services.download import main as download_main
from src.services.filter import main as filter_main

logger = get_logger(__name__)


def run_download_filter(args: argparse.Namespace) -> int:
    """
    Execute the download and filter pipeline stages sequentially.
    
    1. Downloads the raw dataset to data/raw/
    2. Filters the dataset by category and saves to data/filtered/
    """
    logger.info("Starting download-filter pipeline")
    
    # Stage 1: Download
    logger.info("Stage 1: Downloading dataset...")
    # Simulate passing args to the download main if it expects specific structure
    # The download_main expects no args in its current signature, but we pass context if needed
    try:
        download_main()
        logger.info("Download stage completed successfully.")
    except Exception as e:
        logger.error(f"Download stage failed: {e}")
        return 1

    # Stage 2: Filter
    logger.info("Stage 2: Filtering dataset...")
    try:
        filter_main()
        logger.info("Filter stage completed successfully.")
    except Exception as e:
        logger.error(f"Filter stage failed: {e}")
        return 1

    logger.info("Download-filter pipeline completed successfully.")
    return 0


def run_score(args: argparse.Namespace) -> int:
    """Placeholder for scoring stage (T021)."""
    logger.warning("Scoring stage not yet implemented.")
    return 0


def run_analyze(args: argparse.Namespace) -> int:
    """Placeholder for analysis stage (T030)."""
    logger.warning("Analysis stage not yet implemented.")
    return 0


def run_all(args: argparse.Namespace) -> int:
    """Run the full pipeline (Download -> Filter -> Score -> Analyze)."""
    logger.info("Running full pipeline...")
    
    # Run download-filter
    if run_download_filter(args) != 0:
        logger.error("Pipeline failed at download-filter stage.")
        return 1
        
    # Run score
    if run_score(args) != 0:
        logger.error("Pipeline failed at score stage.")
        return 1
        
    # Run analyze
    if run_analyze(args) != 0:
        logger.error("Pipeline failed at analyze stage.")
        return 1
        
    logger.info("Full pipeline completed successfully.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="llmXive Automated Science Pipeline CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Pipeline stages")

    # download-filter command
    parser_download = subparsers.add_parser(
        "download-filter", help="Download raw data and filter by category"
    )
    parser_download.set_defaults(func=run_download_filter)

    # score command
    parser_score = subparsers.add_parser(
        "score", help="Compute Logic and Fidelity scores"
    )
    parser_score.set_defaults(func=run_score)

    # analyze command
    parser_analyze = subparsers.add_parser(
        "analyze", help="Perform statistical correlation analysis"
    )
    parser_analyze.set_defaults(func=run_analyze)

    # all command
    parser_all = subparsers.add_parser(
        "all", help="Run the full pipeline"
    )
    parser_all.set_defaults(func=run_all)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Setup logging
    setup_logging(level=logging.INFO)

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())