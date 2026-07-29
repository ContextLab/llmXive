import sys
import logging
import argparse
from pathlib import Path
from data_cleaning import run_cleaning_pipeline
from logging_config import setup_logging, get_logger
from config import get_config

def main():
    """CLI wrapper for the cleaning pipeline."""
    setup_logging()
    logger = get_logger(__name__)
    
    parser = argparse.ArgumentParser(description="Run data cleaning pipeline")
    parser.add_argument("--check-only", action="store_true", help="Run validation checks only")
    args = parser.parse_args()
    
    try:
        config = get_config()
        raw_path = Path(config.data_raw_dir) / "openml_aluminum.json"
        output_path = Path(config.data_processed_dir) / "filtered_alloys.csv"
        
        if args.check_only:
            logger.info("Running check-only mode (schema validation only)...")
            if not raw_path.exists():
                raise FileNotFoundError(f"Raw data not found at {raw_path}")
            # Just load and validate schema
            from data_cleaning import load_raw_data, apply_schema_validation
            records = load_raw_data(raw_path)
            apply_schema_validation(records)
            logger.info("Check-only passed.")
        else:
            logger.info("Running full cleaning pipeline...")
            df = run_cleaning_pipeline(raw_path, output_path)
            logger.info(f"Pipeline completed. Rows: {len(df)}")
            
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
