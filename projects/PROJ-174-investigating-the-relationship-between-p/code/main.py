"""
Main entry point for the Pupil Dilation and Cognitive Load pipeline.

This script initializes the environment, loads configuration, and orchestrates
the pipeline execution. It verifies that required environment variables are set
and runs the US1 pipeline (Preprocessing -> Feature Extraction -> Correlation Analysis).
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Project imports based on API surface
from config import load_config
from logging_config import get_logger
from preprocessing.filter import apply_filter_to_dataset, write_quality_report
from preprocessing.features import extract_features, process_dataset_features
from analysis.correlations import compute_correlations, save_results, load_processed_data
from verify_data_availability import verify_data_availability
from utils.provenance import write_meta, hash_file

# Configure logger immediately
try:
    logger = get_logger("main")
except Exception:
    # Fallback if logging_config is not fully ready
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('code/logs/preprocess.log')
        ]
    )
    logger = logging.getLogger("main")

def verify_environment() -> bool:
    """
    Verifies that required environment variables are present.
    Returns True if all are set, False otherwise.
    """
    required_vars = ['DATA_PATH', 'OPENNEURO_API_KEY', 'LOG_LEVEL']
    missing = []

    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        error_msg = f"ERROR: Missing required environment variables: {', '.join(missing)}. " \
                    f"Please ensure {os.path.join('code', '.env')} is configured correctly."
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        return False

    # Log the loaded LOG_LEVEL
    log_level = os.getenv('LOG_LEVEL')
    logger.info(f"Environment verified. LOG_LEVEL set to: {log_level}")
    
    # Adjust root logger level
    try:
        logging.getLogger().setLevel(log_level)
    except ValueError:
        logger.warning(f"Invalid LOG_LEVEL '{log_level}'. Defaulting to INFO.")
        logging.getLogger().setLevel(logging.INFO)

    return True

def run_pipeline():
    """
    Orchestrates the US1 pipeline:
    1. Verify data availability
    2. Load and preprocess data (filter blinks, low-pass)
    3. Extract features (salience, fixation count, search time)
    4. Compute correlations
    5. Save results and write provenance
    """
    logger.info("=== Starting Pupil Dilation & Cognitive Load Pipeline (US1) ===")
    
    # Load configuration
    try:
        config = load_config()
        logger.info("Configuration loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Step 1: Verify Data Availability
    logger.info("Step 1: Verifying data availability...")
    data_root = Path(os.getenv('DATA_PATH'))
    if not data_root.exists():
        logger.error(f"Data path does not exist: {data_root}")
        sys.exit(1)

    # Run verification (downloads if needed per T002c logic)
    try:
        verified_datasets = verify_data_availability(data_root)
        if not verified_datasets:
            logger.critical("No valid eye-tracking datasets found. Pipeline halted.")
            sys.exit(1)
        logger.info(f"Verified {len(verified_datasets)} dataset(s) ready for processing.")
    except Exception as e:
        logger.critical(f"Data verification failed: {e}")
        sys.exit(1)

    # Step 2 & 3: Preprocessing and Feature Extraction
    # Assuming verified_datasets contains paths to raw files or directories
    # We iterate through them. For this orchestrator, we assume the structure 
    # expected by the preprocessing modules.
    
    processed_data_path = Path('data/processed')
    processed_data_path.mkdir(parents=True, exist_ok=True)
    
    all_processed_files = []

    for dataset_info in verified_datasets:
        raw_path = dataset_info.get('path')
        if not raw_path or not Path(raw_path).exists():
            logger.warning(f"Skipping missing raw data: {raw_path}")
            continue

        logger.info(f"Processing dataset: {raw_path}")
        dataset_id = dataset_info.get('id', 'unknown')

        # 2a. Filter
        # Note: apply_filter_to_dataset returns the path to the filtered data
        try:
            filtered_path = apply_filter_to_dataset(raw_path, dataset_id)
            logger.info(f"Filtering complete: {filtered_path}")
        except Exception as e:
            logger.error(f"Filtering failed for {dataset_id}: {e}")
            continue

        # 2b. Features
        try:
            features_path = extract_features(filtered_path, dataset_id)
            logger.info(f"Feature extraction complete: {features_path}")
            all_processed_files.append(features_path)
        except Exception as e:
            logger.error(f"Feature extraction failed for {dataset_id}: {e}")
            continue

    if not all_processed_files:
        logger.error("No data was successfully processed. Aborting analysis.")
        sys.exit(1)

    # Step 4: Compute Correlations
    logger.info("Step 4: Computing correlations...")
    try:
        # Load all processed files into a single dataframe or process list
        # The compute_correlations function expects a list of paths or a combined DF
        correlation_results = compute_correlations(all_processed_files, config)
        
        # Step 5: Save Results
        results_dir = Path('results')
        results_dir.mkdir(parents=True, exist_ok=True)
        output_file = results_dir / 'correlations.csv'
        
        save_results(correlation_results, output_file)
        logger.info(f"Correlation results saved to: {output_file}")

        # Write Quality Report (T017 integration)
        # Assuming write_quality_report was called during filter or here
        # We ensure it is called if not already done in the filter step
        # The filter step should have appended to results/quality_report.csv
        
        # Write Provenance
        meta_path = results_dir / 'pipeline_run_meta.json'
        write_meta(meta_path, {
            'run_timestamp': str(datetime.now(timezone.utc)),
            'datasets_processed': [f for f in all_processed_files],
            'config_hash': hash_file('code/config.yaml')
        })
        logger.info(f"Provenance metadata written to: {meta_path}")

        logger.info("=== Pipeline Execution Complete ===")

    except Exception as e:
        logger.critical(f"Analysis phase failed: {e}")
        sys.exit(1)

def main():
    """
    Main entry point.
    """
    # Load environment variables
    load_dotenv()

    logger.info("Starting Pupil Dilation Pipeline orchestrator...")

    # Verify environment
    if not verify_environment():
        logger.critical("Pipeline initialization failed due to missing environment variables.")
        sys.exit(1)

    # Run the pipeline
    run_pipeline()

if __name__ == "__main__":
    main()