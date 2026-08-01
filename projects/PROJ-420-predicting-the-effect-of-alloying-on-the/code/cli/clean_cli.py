"""
CLI entry point for data cleaning (T046).
Orchestrates the data cleaning steps (T010, T014, T011, T012, T013, T018).
Callable via: python -m code.cli.clean_cli --clean
"""
import sys
import logging
import argparse
from pathlib import Path

# Add project root to path to allow relative imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from logging_config import setup_logging, get_logger
from config import get_config
from data_cleaning import run_cleaning_pipeline

def main():
    """Main entry point for the data cleaning CLI."""
    parser = argparse.ArgumentParser(
        description="CLI entry point for data cleaning pipeline (T046)."
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Run the full data cleaning pipeline.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Run validation checks without writing output (for debugging).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(log_level=log_level)
    logger.info("Starting data cleaning CLI (T046)...")

    try:
        config = get_config()
        logger.info(f"Configuration loaded from {config.config_file_path}")

        if args.check_only:
            logger.info("Running in check-only mode...")
            # Perform checks without writing output
            # This is a placeholder for validation logic if needed
            # For now, we just verify the pipeline can be imported and configured
            logger.info("Check-only mode: Pipeline configuration verified.")
            return 0

        if args.clean:
            logger.info("Running full data cleaning pipeline...")
            # Run the core cleaning logic
            success = run_cleaning_pipeline(config)
            if success:
                logger.info("Data cleaning pipeline completed successfully.")
                return 0
            else:
                logger.error("Data cleaning pipeline failed.")
                return 1
        else:
            parser.print_help()
            return 0

    except Exception as e:
        logger.exception(f"Data cleaning CLI failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())