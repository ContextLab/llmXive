"""
Main orchestrator for the Pollinator Network Prediction Pipeline.

This script sequentially runs the data ingestion and preprocessing stages.
It depends on the validation logic implemented in T020.
"""
import sys
import logging
from pathlib import Path

# Add project root to path to ensure imports work regardless of CWD
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import ensure_directories_exist, get_data_raw, get_data_processed, get_results_root, get_logs_root
from utils.logger import setup_logging, get_logger
from utils.io_utils import ensure_directory_structure
from ingestion import WebOfLifeDownloader
from preprocessing import build_feature_matrix, save_feature_matrix

def main():
    """
    Orchestrates the ingestion and preprocessing pipeline.
    
    1. Ensures directory structure exists.
    2. Initializes the WebOfLifeDownloader.
    3. Runs ingestion (downloads data).
    4. Runs preprocessing (builds feature matrix).
    5. Logs final counts and success status.
    """
    # Setup logging
    log_dir = get_logs_root()
    ensure_directory_structure(log_dir)
    setup_logging(log_level=logging.INFO, log_file=log_dir / "main_pipeline.log")
    logger = get_logger("main_orchestrator")
    
    logger.info("Starting Pollinator Network Prediction Pipeline (T021 Orchestrator)")

    try:
        # 1. Ensure directory structure
        logger.info("Ensuring directory structure...")
        ensure_directories_exist()
        
        raw_dir = get_data_raw()
        processed_dir = get_data_processed()
        results_dir = get_results_root()
        
        logger.info(f"Raw data directory: {raw_dir}")
        logger.info(f"Processed data directory: {processed_dir}")
        
        # 2. Initialize Downloader
        logger.info("Initializing WebOfLifeDownloader...")
        downloader = WebOfLifeDownloader()
        
        # 3. Run Ingestion
        # T012 requirement: Must return the count of valid ecosystems retrieved.
        # T020 requirement: Validation logic checks this count (warn if < 8).
        logger.info("Running data ingestion...")
        valid_ecosystem_count = downloader.run_ingestion_pipeline()
        
        logger.info(f"Ingestion complete. Valid ecosystems retrieved: {valid_ecosystem_count}")
        
        # T020 logic is embedded in the downloader/ingestion flow or called here.
        # Assuming downloader.run_ingestion_pipeline() handles the T020 validation logic
        # internally as per the dependency chain, or we log the result here.
        # Based on T020 description: "If valid_count < 8, log a warning...".
        # The ingestion script (T012) returns the count. We log it here.
        if valid_ecosystem_count < 8:
            logger.warning(f"Reduced sample size detected: {valid_ecosystem_count} ecosystems (threshold: 8). Proceeding with available data.")
        
        if valid_ecosystem_count == 0:
            logger.error("No valid ecosystems retrieved. Cannot proceed with preprocessing.")
            return 1

        # 4. Run Preprocessing
        # T014-T019: Co-occurrence, Negative Samples, Imputation, Normalization, Encoding, Matrix Construction.
        # T020: Validation & Threshold Enforcement (already checked count above).
        logger.info("Running preprocessing pipeline...")
        
        feature_matrix_path = processed_dir / "feature_matrix.csv"
        
        # Call the main preprocessing function that builds and saves the matrix
        # This function encapsulates T014-T019 logic.
        matrix_df = build_feature_matrix(raw_dir=raw_dir)
        
        if matrix_df is None or matrix_df.empty:
            logger.error("Preprocessing failed to generate a valid feature matrix.")
            return 1
        
        save_feature_matrix(matrix_df, feature_matrix_path)
        
        logger.info(f"Feature matrix saved to: {feature_matrix_path}")
        logger.info(f"Matrix shape: {matrix_df.shape}")
        logger.info(f"Columns: {list(matrix_df.columns)}")

        logger.info("Pipeline completed successfully.")
        return 0

    except Exception as e:
        logger.exception(f"Pipeline failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
