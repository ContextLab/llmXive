"""
CLI entry point for data extraction.
Orchestrates fetching from Materials Project and NIST.
"""
import sys
import logging
import argparse
from pathlib import Path

# Local imports
from logging_config import setup_logging, get_logger
from config import get_config
from data._download_logic import run_extraction

def main():
    parser = argparse.ArgumentParser(description="Download raw data")
    parser.add_argument("--input", type=str, default=None, help="Input (not used for download)")
    parser.add_argument("--output", type=str, default=None, help="Output (not used for download)")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    
    args = parser.parse_args()

    # Setup logger
    logger = setup_logging(level=args.log_level)
    logger.info("Starting data extraction")

    try:
        # Run extraction
        run_extraction()
        
        logger.info("Extraction complete")
        return 0
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
