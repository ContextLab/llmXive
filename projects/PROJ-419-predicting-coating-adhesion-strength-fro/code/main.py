"""
Main orchestration script for the Coating Adhesion Pipeline.
"""
import os
import sys
import logging
import yaml
import json
import time
import pandas as pd

# Add code directory to path if not already there
code_dir = os.path.dirname(os.path.abspath(__file__))
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from utils import check_halt_signal, ensure_state_dir, write_halt_signal, setup_logging
from ingestion import process_ingestion_data, align_records_strictly, exclude_missing_surface_roughness
from preprocessing import create_preprocessing_pipeline
from modeling import run_modeling_pipeline, run_sensitivity_analysis_crosslinker_proxy
from evaluation import run_baseline_evaluation_pipeline
from config import DATA_PROCESSED_DIR, STATE_DIR, TIMEOUT_HOURS, MAX_ROWS

logger = logging.getLogger(__name__)

def check_data_source_verification():
    """
    Check the data source verification report.
    If any source is invalid, write HALT_SIGNAL.yaml and exit.
    """
    report_path = os.path.join(DATA_PROCESSED_DIR, "data_source_verification_report.json")
    
    if not os.path.exists(report_path):
        logger.error(f"Data source verification report not found at {report_path}.")
        write_halt_signal("Data source verification report missing.")
        return False

    try:
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        # Check if any source is invalid (status != 0)
        invalid_sources = []
        for source, status in report.items():
            if status != 0:
                invalid_sources.append(source)
        
        if invalid_sources:
            logger.error(f"Data source verification failed for: {invalid_sources}")
            write_halt_signal(f"Invalid data sources: {invalid_sources}")
            return False
        
        logger.info("Data source verification passed.")
        return True

    except json.JSONDecodeError:
        logger.error("Failed to parse data source verification report.")
        write_halt_signal("Invalid data source verification report format.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking data source verification: {e}")
        write_halt_signal(f"Error checking data source verification: {e}")
        return False

def save_unified_dataset():
    """
    Save the unified coating adhesion dataset to data/processed/.
    This implements T031: Orchestration to save unified dataset.
    """
    logger.info("Saving unified coating adhesion dataset...")
    
    # The ingestion module should have already processed and aligned data.
    # We expect the aligned data to be available in memory or a temporary file.
    # For this implementation, we assume process_ingestion_data() prepares the data
    # and we need to write it to the final CSV.
    
    # Note: In a real pipeline, the data would be passed between stages.
    # Here we rely on the ingestion module to have prepared the data.
    # We'll re-load the processed data from the ingestion step if it was saved there,
    # or we assume the ingestion step writes to a temporary location.
    
    # Since the ingestion logic is in process_ingestion_data, we need to ensure
    # the data is available. Let's assume the ingestion module saves intermediate
    # aligned data to a temporary file that we can load and save as the final dataset.
    
    # For T031, we are responsible for writing the final unified CSV.
    # We assume the ingestion pipeline has created a unified dataframe.
    
    # Re-run ingestion to get the data (or load from cache if implemented)
    # This is a simplification; in a real system, data would be passed via objects or a database.
    
    # Call ingestion to ensure data is ready (it should handle caching internally if needed)
    process_ingestion_data()
    
    # The ingestion module should have saved the aligned data.
    # We need to load it and save it as the final unified dataset.
    # Let's assume the ingestion module saves to a temp file or we can access the data.
    
    # For this implementation, we'll assume the ingestion module has a function
    # to retrieve the final aligned dataframe. If not, we'll need to adjust.
    
    # Since we don't have a direct way to get the dataframe here, we'll assume
    # the ingestion module saves the aligned data to a specific file that we can load.
    
    # Let's define the expected path for the aligned data from ingestion
    aligned_data_path = os.path.join(DATA_PROCESSED_DIR, "aligned_coating_data.csv")
    
    if os.path.exists(aligned_data_path):
        df = pd.read_csv(aligned_data_path)
        
        # Save to the final unified dataset location
        output_path = os.path.join(DATA_PROCESSED_DIR, "coating_adhesion_dataset.csv")
        df.to_csv(output_path, index=False)
        logger.info(f"Unified dataset saved to {output_path}")
        return True
    else:
        logger.error(f"Aligned data not found at {aligned_data_path}")
        write_halt_signal("Aligned data not found after ingestion.")
        return False

def run_pipeline():
    """
    Execute the full pipeline.
    """
    logger.info("Starting Coating Adhesion Pipeline...")
    start_time = time.time()

    # 1. Check Data Source Verification (T093)
    logger.info("Step 0: Checking Data Source Verification...")
    if not check_data_source_verification():
        logger.error("Pipeline halted due to data source verification failure.")
        return 1

    # 2. Check Halt Signal
    if check_halt_signal():
        logger.error("Pipeline halted due to previous error.")
        return 1

    # 3. Ingestion
    logger.info("Step 1: Data Ingestion...")
    process_ingestion_data()
    if check_halt_signal():
        return 1

    # 4. Save Unified Dataset (T031)
    logger.info("Step 1.5: Saving Unified Dataset (T031)...")
    if not save_unified_dataset():
        logger.error("Pipeline halted due to failure to save unified dataset.")
        return 1

    # 5. Preprocessing
    logger.info("Step 2: Preprocessing...")
    create_preprocessing_pipeline()
    if check_halt_signal():
        return 1

    # 6. Sensitivity Analysis (T041)
    logger.info("Step 3: Sensitivity Analysis (T041)...")
    run_sensitivity_analysis_crosslinker_proxy()
    if check_halt_signal():
        return 1

    # 7. Modeling
    logger.info("Step 4: Modeling...")
    run_modeling_pipeline()
    if check_halt_signal():
        return 1

    # 8. Evaluation
    logger.info("Step 5: Evaluation...")
    run_baseline_evaluation_pipeline()
    if check_halt_signal():
        return 1

    # 9. Final Report
    elapsed = time.time() - start_time
    logger.info(f"Pipeline completed successfully in {elapsed:.2f} seconds.")
    
    # Write completion signal
    ensure_state_dir()
    with open(os.path.join(STATE_DIR, 'pipeline_complete.yaml'), 'w') as f:
        yaml.dump({'status': 'complete', 'runtime_seconds': elapsed}, f)
    
    return 0

def main():
    """Main entry point."""
    setup_logging()
    exit_code = run_pipeline()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
