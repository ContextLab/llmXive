"""
Main orchestration script for the sleep quality prediction pipeline.
Coordinates data download, preprocessing, feature engineering, and modeling.
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Import orchestration targets
from data.download_hcp import main as download_main, filter_subjects
from data.preprocess import main as preprocess_main
from data.feature_engineering import main as feature_main
from modeling.train import main as train_main
from modeling.evaluate import main as evaluate_main
from modeling.report_generator import main as report_main
from modeling.interpret import main as interpret_main
from modeling.finalize_report import main as finalize_main

from config import get_paths, ensure_dirs
from utils.logging import setup_logging, log_stage_start, log_stage_complete, log_stage_error

def run_pipeline():
    """
    Orchestrate the full end-to-end research pipeline:
    1. Download raw HCP data
    2. Filter subjects based on behavioral criteria
    3. Preprocess fMRI data (Schaefer parcellation, nuisance regression, filtering)
    4. Engineer connectivity features (correlation, Fisher-z, vectorization)
    5. Train predictive models
    6. Evaluate with permutation tests and bootstrap
    7. Interpret results and generate reports
    """
    start_time = time.time()
    paths = get_paths()
    ensure_dirs()

    # Setup logging
    logger = setup_logging()
    log_stage_start("Pipeline", "Starting full research pipeline execution")

    try:
        # --- Stage 1: Data Acquisition ---
        log_stage_start("Data Ingestion", "Fetching HCP minimally preprocessed data and behavioral files")
        download_main()
        log_stage_complete("Data Ingestion", "Raw data downloaded successfully")

        # --- Stage 2: Subject Filtering ---
        log_stage_start("Subject Filtering", "Identifying valid subjects and excluding high motion")
        # This updates the internal state or file markers used by subsequent stages
        # We assume filter_subjects prepares the list of valid IDs for downstream steps
        valid_subjects = filter_subjects()
        log_stage_complete("Subject Filtering", f"Filtered to {len(valid_subjects)} valid subjects")

        # --- Stage 3: Preprocessing ---
        log_stage_start("Preprocessing", "Running Schaefer parcellation and nuisance regression")
        preprocess_main()
        log_stage_complete("Preprocessing", "Time series extracted and cleaned")

        # --- Stage 4: Feature Engineering ---
        log_stage_start("Feature Engineering", "Computing connectivity matrices and vectorizing")
        feature_main()
        log_stage_complete("Feature Engineering", "Feature vectors saved to data/processed/")

        # --- Stage 5: Modeling ---
        log_stage_start("Modeling", "Training ElasticNet models with nested CV")
        train_main()
        log_stage_complete("Modeling", "Model training complete; predictions saved")

        # --- Stage 6: Evaluation ---
        log_stage_start("Evaluation", "Running permutation tests and bootstrap analysis")
        evaluate_main()
        log_stage_complete("Evaluation", "Statistical validation complete")

        # --- Stage 7: Interpretation ---
        log_stage_start("Interpretation", "Extracting non-zero coefficients and mapping edges")
        interpret_main()
        log_stage_complete("Interpretation", "Brain connectivity map generated")

        # --- Stage 8: Reporting ---
        log_stage_start("Reporting", "Generating final ResultReport.json")
        report_main()
        finalize_main()
        log_stage_complete("Reporting", "Final report generated")

        log_stage_complete("Pipeline", "Full pipeline execution successful")
        return True

    except Exception as e:
        log_stage_error("Pipeline", str(e))
        # Re-raise to ensure the script exits with non-zero status
        raise e

if __name__ == "__main__":
    success = run_pipeline()
    if success:
        print("Pipeline completed successfully.")
        sys.exit(0)
    else:
        print("Pipeline failed.")
        sys.exit(1)
