"""
Main entry point for the HEA Yield Strength Prediction Pipeline.
Orchestrates the full execution: Data -> Descriptors -> Training -> Validation -> Report.
"""
import os
import sys
import json
import time
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger, set_seeds
from data.download import download_dataset
from data.pipeline import run_pipeline
from data.status_writer import write_data_status
from models.train import run_training_pipeline
from models.evaluate import run_evaluation_pipeline
from models.metrics_writer import write_metrics_json
from models.power_analysis import write_power_analysis
from models.report_generator import main as generate_report_main
from models.runtime_tracker import track_runtime, save_runtime
from utils.report_utils import inject_disclaimer, finalize_report_markdown

logger = get_logger(__name__)

def main():
    """Execute the full research pipeline."""
    start_time = time.time()
    logger.info("Starting HEA Yield Strength Prediction Pipeline")

    # 1. Setup
    set_seeds(seed=42)
    project_root = Path(__file__).resolve().parent
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Data Acquisition & Processing (US1)
    logger.info("Phase 1: Data Acquisition and Descriptor Engineering")
    # T008: Download
    data_status = download_dataset()
    
    # T014/T015: Run pipeline and write status
    # If download returned NO_DATA, the pipeline might handle it or we skip
    if data_status.get("status") != "NO_DATA":
        processed_df = run_pipeline()
        status_info = write_data_status(processed_df)
    else:
        # Handle empty data case
        status_info = write_data_status(None)
        logger.warning("No data found. Generating empty status.")
    
    # 3. Model Training (US2)
    logger.info("Phase 2: Model Training and Evaluation")
    run_training_pipeline()
    
    # 4. Statistical Validation (US3)
    logger.info("Phase 3: Statistical Validation")
    run_evaluation_pipeline()
    
    # 5. Report Generation (T041)
    logger.info("Phase 4: Report Generation")
    generate_report_main()
    
    # 6. Runtime Tracking (T022)
    total_time = time.time() - start_time
    save_runtime(total_time)
    
    logger.info(f"Pipeline completed successfully in {total_time:.2f} seconds.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
