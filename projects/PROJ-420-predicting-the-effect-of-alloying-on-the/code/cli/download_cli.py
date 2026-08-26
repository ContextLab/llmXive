"""
CLI for data extraction.
"""
import sys
import logging
import argparse
from pathlib import Path
from logging_config import setup_logging, get_logger
from config import get_config

logger = get_logger(__name__)

def main():
    """Entry point for download CLI."""
    parser = argparse.ArgumentParser(description="Download raw data for alloy analysis")
    parser.add_argument("--extract", action="store_true", help="Run data extraction")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args()
    
    # Setup logging with tolerant function
    logger = setup_logging(level=args.log_level)
    
    if args.extract:
        from data._download_logic import run_extraction
        run_extraction()
    else:
        logger.info("Use --extract to run data extraction")

if __name__ == "__main__":
    main()
