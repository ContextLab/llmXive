import os
import sys
import logging
import json
import pandas as pd
from pathlib import Path

# Add project root to path to ensure imports work regardless of cwd
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ingestion.load_literature_data import load_and_merge_sources
from ingestion.handle_missing_data import handle_missing_data
from ingestion.flag_high_variance import flag_high_variance_entries, save_results as save_variance_results
from ingestion.validate_dataset import validate_dataset
from utils.logging_config import setup_pipeline_logger, log_event
from utils.errors import DataInsufficientError

def main():
    """
    Orchestrates the generation of data/processed/standardized_polymers.csv.
    
    Steps:
    1. Load and merge all literature sources (manual + automated).
    2. Handle missing data (imputation or halt).
    3. Flag and exclude high-variance entries.
    4. Validate the resulting dataset (count >= 30, bio-membranes >= 10).
    5. Save the final standardized CSV.
    """
    logger = setup_pipeline_logger("T016_generate_standardized_csv")
    log_event(logger, "INFO", "Starting standardized CSV generation pipeline")

    try:
        # Step 1: Load and merge sources
        logger.info("Loading and merging literature sources...")
        df_merged = load_and_merge_sources()
        
        if df_merged is None or df_merged.empty:
            log_event(logger, "ERROR", "No data loaded from sources. Pipeline halted.")
            return

        log_event(logger, "INFO", f"Loaded {len(df_merged)} raw records")

        # Step 2: Handle missing data
        logger.info("Handling missing data (imputation/halt)...")
        df_imputed, missing_report = handle_missing_data(df_merged)
        
        if df_imputed is None:
            log_event(logger, "ERROR", "Data insufficient after missing data check. Pipeline halted.")
            return

        log_event(logger, "INFO", f"Processed {len(df_imputed)} records after imputation")

        # Step 3: Flag and exclude high variance entries
        logger.info("Flagging and excluding high variance entries...")
        df_clean, variance_report = flag_high_variance_entries(df_imputed)
        
        if df_clean is None:
            log_event(logger, "ERROR", "No valid records remaining after variance filtering.")
            return

        log_event(logger, "INFO", f"Remaining {len(df_clean)} records after variance filtering")

        # Step 4: Validate dataset
        logger.info("Validating dataset constraints...")
        validation_result = validate_dataset(df_clean)
        
        if not validation_result.get("is_valid", False):
            error_msg = validation_result.get("reason", "Validation failed")
            log_event(logger, "ERROR", f"Dataset validation failed: {error_msg}")
            # Do not save if validation fails to prevent corrupted artifacts
            raise DataInsufficientError(f"Dataset validation failed: {error_msg}")

        log_event(logger, "INFO", "Dataset validation passed")

        # Step 5: Save the final standardized CSV
        output_path = Path("data/processed/standardized_polymers.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df_clean.to_csv(output_path, index=False)
        log_event(logger, "INFO", f"Saved standardized data to {output_path}")
        
        # Save reports generated during the process
        if missing_report:
            with open("data/processed/missing_data_report.json", "w") as f:
                json.dump(missing_report, f, indent=2)
        
        if variance_report:
            # Ensure save_variance_results was called, or save here if needed
            # Assuming flag_high_variance_entries handles its own saving or returns report
            pass

        log_event(logger, "SUCCESS", "T016 Completed: Standardized CSV generated successfully")

    except DataInsufficientError as e:
        logger.error(f"Pipeline halted due to data insufficiency: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during pipeline execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()