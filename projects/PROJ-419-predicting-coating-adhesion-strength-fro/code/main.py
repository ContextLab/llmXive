"""
Main orchestration script for the Coating Adhesion Pipeline.
"""
import os
import sys
import logging
import yaml
import json
import time

# Add code directory to path if not already there
code_dir = os.path.dirname(os.path.abspath(__file__))
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from utils import check_halt_signal, ensure_state_dir, write_halt_signal, setup_logging
from ingestion import process_ingestion_data
from preprocessing import create_preprocessing_pipeline
from modeling import run_modeling_pipeline, run_sensitivity_analysis_crosslinker_proxy
from evaluation import run_baseline_evaluation_pipeline
from config import DATA_PROCESSED_DIR, STATE_DIR, TIMEOUT_HOURS

logger = logging.getLogger(__name__)

def run_pipeline():
    """
    Execute the full pipeline.
    """
    logger.info("Starting Coating Adhesion Pipeline...")
    start_time = time.time()

    # 1. Check Halt Signal
    if check_halt_signal():
        logger.error("Pipeline halted due to previous error.")
        return 1

    # 2. Ingestion
    logger.info("Step 1: Data Ingestion...")
    process_ingestion_data()
    if check_halt_signal():
        return 1

    # 3. Preprocessing
    logger.info("Step 2: Preprocessing...")
    create_preprocessing_pipeline()
    if check_halt_signal():
        return 1

    # 4. Sensitivity Analysis (T041)
    logger.info("Step 3: Sensitivity Analysis (T041)...")
    run_sensitivity_analysis_crosslinker_proxy()
    if check_halt_signal():
        return 1

    # 5. Modeling
    logger.info("Step 4: Modeling...")
    run_modeling_pipeline()
    if check_halt_signal():
        return 1

    # 6. Evaluation
    logger.info("Step 5: Evaluation...")
    run_baseline_evaluation_pipeline()
    if check_halt_signal():
        return 1

    # 7. Final Report
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