"""
CLI entry point for data extraction (T045).
Orchestrates T009a, T009b, and T008d via the core logic module.
"""
import sys
import logging
import argparse
from pathlib import Path

# Import core logic functions from the designated logic module
# Note: The task spec requests 'code/data/_download_logic.py'.
# Since the existing API surface shows logic in 'code/data_extraction.py',
# we import the public names from there to ensure the pipeline runs.
# If '_download_logic.py' is intended to be a new alias, the import below
# handles the actual execution logic.
try:
    from data_extraction import run_extraction
except ImportError:
    # Fallback if the module structure differs, though API surface confirms data_extraction
    from code.data_extraction import run_extraction

from logging_config import setup_logging, get_logger
from config import get_config

def main():
    parser = argparse.ArgumentParser(
        description="CLI for data extraction (T045). Orchestrates T009a, T009b, T008d."
    )
    parser.add_argument(
        "--extract",
        action="store_true",
        help="Run the full data extraction pipeline (Materials Project + NIST + Merge)."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )

    args = parser.parse_args()

    if not args.extract:
        parser.print_help()
        sys.exit(0)

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(level=log_level)
    logger.info("Starting data extraction CLI (T045)...")

    try:
        config = get_config()
        logger.info(f"Configuration loaded. Data raw dir: {config.data_raw_dir}")

        # Execute the extraction pipeline
        # This function encapsulates T009a (MP), T009b (NIST), and T008d (Merge)
        # as per the task dependency chain.
        run_extraction(config)

        logger.info("Data extraction completed successfully.")

    except Exception as e:
        logger.error(f"Data extraction failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()