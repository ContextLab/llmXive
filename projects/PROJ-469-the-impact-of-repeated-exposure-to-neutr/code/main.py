"""
Main orchestration script for the Political News Exposure Analysis Pipeline.
Executes all stages: Data Fetch -> Preprocessing -> Primary Model -> Robustness -> Reporting.
"""
import sys
import os
from pathlib import Path
import logging

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

logger = get_logger(__name__)

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

        # 3. Preprocessing (T013, T014, T016)
        logger.info("Step 3: Preprocessing and Imputation...")
        imputed_data_path = run_preprocessing_pipeline()
        logger.info(f"Imputed data saved to: {imputed_data_path}")

        # 4. Primary Model (T015)
        logger.info("Step 4: Running Primary Analysis...")
        run_primary_analysis()
        logger.info("Primary model fitted and saved.")

        # 5. Covariate Model (T023)
        logger.info("Step 5: Running Covariate Analysis...")
        run_covariate_analysis()
        logger.info("Covariate model fitted and saved.")

        # 6. Binary Model (T024b)
        logger.info("Step 6: Running Binary Model Analysis...")
        run_binary_model_pipeline()
        logger.info("Binary model fitted and saved.")

        # 7. Robustness Checks (T021a, T022, T021c)
        logger.info("Step 7: Running Robustness Checks (Bootstrap & Alpha Sweep)...")
        run_robustness_pipeline()
        logger.info("Robustness checks complete.")

        # 8. Aggregate Robustness (T025 Integration)
        logger.info("Step 8: Aggregating Robustness Metrics...")
        run_aggregation_pipeline()
        logger.info("Robustness aggregation complete.")

        # 9. Power Analysis (T017b)
        logger.info("Step 9: Running Retrospective Power Analysis...")
        run_power_pipeline()
        logger.info("Power analysis complete.")

        # 10. Summary Aggregation (T029)
        logger.info("Step 10: Aggregating Summary Tables...")
        run_summary_aggregation_pipeline()
        logger.info("Summary aggregation complete.")

        # 11. Reporting (T028b, T030, T031)
        logger.info("Step 11: Generating Report...")
        run_reporting_pipeline()
        logger.info("Report generation complete.")

        # 12. Validation (T032)
        logger.info("Step 12: Validating Results...")
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
