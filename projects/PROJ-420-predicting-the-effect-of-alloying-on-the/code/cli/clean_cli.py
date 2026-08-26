"""CLI for data cleaning."""
import sys
import logging
import argparse
from pathlib import Path
from logging_config import setup_logging, get_logger
from config import get_config

def main() -> None:
    """Main entry point for clean CLI."""
    parser = argparse.ArgumentParser(description="Clean data")
    parser.add_argument("--pipeline", action="store_true", help="Run cleaning pipeline")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging (tolerant of any call shape)
    logger = setup_logging(log_level=args.log_level)
    
    config = get_config()
    logger.info("Clean CLI started")
    
    if args.pipeline:
        from data.clean import run_cleaning_pipeline
        logger.info("Running cleaning pipeline...")
        run_cleaning_pipeline()
        logger.info("Cleaning pipeline complete")
    else:
        logger.info("No action specified")

if __name__ == "__main__":
    main()