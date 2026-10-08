"""
Main orchestration script for the Political News Exposure Analysis Pipeline.
Executes all stages: Data Fetch -> Preprocessing -> Primary Model -> Robustness -> Reporting.
Includes a "dry-run" schema validation step to ensure column mapping logic works.
"""
import sys
import os
from pathlib import Path
import logging
from typing import List

from logging_config import setup_logging, get_logger
from config import ensure_dirs
from config_manager import get_config, get_data_raw_path, get_data_processed_path, get_results_path

# Import pipeline functions
from data_fetcher import fetch_project_implicit_political_data
from preprocessing import run_preprocessing_pipeline
from models import run_primary_analysis, run_covariate_analysis
from robustness import run_robustness_pipeline
from binary_model import run_binary_model_pipeline
from aggregate_robustness import run_aggregation_pipeline
from aggregate_summary import run_summary_aggregation_pipeline
from reporting import run_reporting_pipeline
from power import run_power_pipeline
from validate_results import run_validation
from data_loader import load_project_implicit_data, check_required_columns

logger = get_logger(__name__)

# Required columns for the analysis based on contract/schema
REQUIRED_COLUMNS: List[str] = [
    "IAT_D_score",
    "political_ideology",
    "news_exposure_freq",
    "age",
    "gender",
    "education"
]

def validate_schema_dry_run(data_path: Path) -> None:
    """
    Performs a 'dry-run' validation of the data schema.
    Loads the first several rows (or entire file if small) to ensure
    column mapping logic works and required columns are present.
    
    Raises:
        ValueError: If required columns are missing or schema validation fails.
    """
    logger.info(f"Performing schema dry-run on: {data_path}")
    
    try:
        # Load a sample to validate schema without processing full dataset if large
        # We load the first 1000 rows to verify structure, or fewer if file is small
        df_sample = load_project_implicit_data(data_path, nrows=1000)
        
        if df_sample.empty:
            raise ValueError("Data file is empty; cannot validate schema.")
        
        logger.info(f"Loaded sample with {len(df_sample)} rows for validation.")
        
        # Check required columns
        missing_cols = check_required_columns(df_sample, REQUIRED_COLUMNS)
        if missing_cols:
            error_msg = f"Schema validation failed. Missing required columns: {missing_cols}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Schema dry-run passed. All required columns present.")
        
    except Exception as e:
        logger.error(f"Schema dry-run failed: {e}", exc_info=True)
        raise

def main():
    """Execute the full analysis pipeline."""
    setup_logging()
    logger.info("="*60)
    logger.info("Starting Political News Exposure Analysis Pipeline")
    logger.info("="*60)

    try:
        # 1. Setup Directories
        logger.info("Step 1: Ensuring directories...")
        ensure_dirs()

        # 2. Data Fetch (T038)
        logger.info("Step 2: Fetching/Validating Data...")
        # This function handles fetching or validating local files
        # It raises an error if no data is found
        data_path = fetch_project_implicit_political_data()
        logger.info(f"Data source validated at: {data_path}")

        # 3. **NEW**: Schema Dry-Run (T041)
        logger.info("Step 3: Performing Schema Dry-Run...")
        validate_schema_dry_run(data_path)
        logger.info("Schema dry-run successful.")

        # 4. Preprocessing (T013, T014, T016)
        logger.info("Step 4: Preprocessing and Imputation...")
        imputed_data_path = run_preprocessing_pipeline()
        logger.info(f"Imputed data saved to: {imputed_data_path}")

        # 5. Primary Model (T015)
        logger.info("Step 5: Running Primary Analysis...")
        run_primary_analysis()
        logger.info("Primary model fitted and saved.")

        # 6. Covariate Model (T023)
        logger.info("Step 6: Running Covariate Analysis...")
        run_covariate_analysis()
        logger.info("Covariate model fitted and saved.")

        # 7. Binary Model (T024b)
        logger.info("Step 7: Running Binary Model Analysis...")
        run_binary_model_pipeline()
        logger.info("Binary model fitted and saved.")

        # 8. Robustness Checks (T021a, T022, T021c)
        logger.info("Step 8: Running Robustness Checks (Bootstrap & Alpha Sweep)...")
        run_robustness_pipeline()
        logger.info("Robustness checks complete.")

        # 9. Aggregate Robustness (T025 Integration)
        logger.info("Step 9: Aggregating Robustness Metrics...")
        run_aggregation_pipeline()
        logger.info("Robustness aggregation complete.")

        # 10. Power Analysis (T017b)
        logger.info("Step 10: Running Retrospective Power Analysis...")
        run_power_pipeline()
        logger.info("Power analysis complete.")

        # 11. Summary Aggregation (T029)
        logger.info("Step 11: Aggregating Summary Tables...")
        run_summary_aggregation_pipeline()
        logger.info("Summary aggregation complete.")

        # 12. Reporting (T028b, T030, T031)
        logger.info("Step 12: Generating Report...")
        run_reporting_pipeline()
        logger.info("Report generation complete.")

        # 13. Validation (T032)
        logger.info("Step 13: Validating Results...")
        run_validation()
        logger.info("Validation complete.")

        logger.info("="*60)
        logger.info("Pipeline completed successfully!")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()