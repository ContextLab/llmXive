"""
CLI Entry Point for Data Cleaning (T046).
Orchestrates the cleaning steps defined in code/data/clean.py.
"""
import sys
import logging
import argparse
from pathlib import Path
from logging_config import setup_logging, get_logger
from config import get_config
from data.clean import run_cleaning_pipeline

def main():
    parser = argparse.ArgumentParser(description="Clean and validate alloy data.")
    parser.add_argument('--input', type=str, required=True, help="Path to raw data file (JSON/CSV)")
    parser.add_argument('--output', type=str, required=True, help="Path to output parquet file")
    parser.add_argument('--log-level', type=str, default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(level=args.log_level)
    logger.log("cleaning_cli_start", level=args.log_level)
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.log("input_not_found", path=str(input_path))
        sys.exit(1)
    
    try:
        run_cleaning_pipeline(input_path, output_path)
        logger.log("cleaning_pipeline_completed", output=str(output_path))
    except SystemExit as e:
        if e.code != 0:
            sys.exit(e.code)
    except Exception as e:
        logger.log("pipeline_failed", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
