import sys
import logging
import argparse
from pathlib import Path
from data_cleaning import run_cleaning_pipeline
from logging_config import setup_logging, get_logger
from config import get_config

def main():
    """CLI wrapper for the cleaning pipeline.
    
    Orchestrates the data cleaning steps (T010, T014, T011, T012, T013)
    as defined in the run-book.
    
    Usage:
        python code/data/clean.py [--check-only]
    """
    setup_logging()
    logger = get_logger(__name__)
    
    parser = argparse.ArgumentParser(
        description="Run data cleaning pipeline (T010, T014, T011, T012, T013)"
    )
    parser.add_argument(
        "--check-only", 
        action="store_true", 
        help="Run validation checks only (schema validation)"
    )
    args = parser.parse_args()
    
    try:
        config = get_config()
        raw_path = Path(config.data_raw_dir) / "openml_aluminum.json"
        output_path = Path(config.data_processed_dir) / "filtered_alloys.csv"
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if args.check_only:
            logger.info("Running check-only mode (schema validation only)...")
            if not raw_path.exists():
                raise FileNotFoundError(
                    f"Raw data not found at {raw_path}. "
                    "Run 'python code/data/download.py' first."
                )
            
            # Just load and validate schema
            from data_cleaning import load_raw_data, apply_schema_validation
            records = load_raw_data(raw_path)
            apply_schema_validation(records)
            logger.info("Check-only passed. Schema is valid.")
            logger.info(f"Loaded {len(records)} records for validation.")
        else:
            logger.info("Running full cleaning pipeline...")
            logger.info(f"Input: {raw_path}")
            logger.info(f"Output: {output_path}")
            
            if not raw_path.exists():
                raise FileNotFoundError(
                    f"Raw data not found at {raw_path}. "
                    "Run 'python code/data/download.py' first."
                )
            
            df = run_cleaning_pipeline(raw_path, output_path)
            
            logger.info(f"Pipeline completed successfully.")
            logger.info(f"Output written to: {output_path}")
            logger.info(f"Rows after cleaning: {len(df)}")
            
            if len(df) == 0:
                logger.error("CRITICAL: No valid entries found after filtering.")
                sys.exit(1)
                
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()