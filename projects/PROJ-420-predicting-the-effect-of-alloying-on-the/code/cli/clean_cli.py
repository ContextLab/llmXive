"""CLI entry point for data cleaning pipeline."""
import sys
import logging
import argparse
from pathlib import Path

from logging_config import setup_logging, get_logger
from config import get_config
from data.clean import run_cleaning_pipeline


def main():
    """Main CLI entry point for data cleaning."""
    parser = argparse.ArgumentParser(description="Clean aluminum alloy data")
    parser.add_argument("--input", type=str, help="Input data file path")
    parser.add_argument("--output", type=str, help="Output data file path")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    # The setup_logging function in logging_config.py is now tolerant of 'level' keyword
    logger = setup_logging(level=args.log_level)
    logger.log("clean_cli_start", input=args.input, output=args.output, log_level=args.log_level)
    
    try:
        # Run cleaning pipeline
        input_path = Path(args.input) if args.input else None
        output_path = Path(args.output) if args.output else None
        
        run_cleaning_pipeline(input_path, output_path)
        
        print("Cleaning complete")
        sys.exit(0)
        
    except Exception as e:
        logger.log("clean_cli_error", error=str(e))
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()