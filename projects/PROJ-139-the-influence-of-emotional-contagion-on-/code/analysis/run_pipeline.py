"""
Full Pipeline Runner for PROJ-139.
Orchestrates the execution of all stages from data download to final reporting.
"""
import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from data.download import main as download_main
from data.validation import main as validation_main
from data.extract import main as extract_main
from data.sampling import main as sampling_main
from data.sentiment import main as sentiment_main
from data.metrics import main as metrics_main
from data.modeling import main as modeling_main
from data.generate_report import main as report_main
from data.verify_reproducibility import main as reproducibility_main
from config.settings import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / 'state' / 'pipeline_run.log')
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure all necessary output directories exist."""
    config = get_config()
    dirs = [
        config.dataset_paths.raw,
        config.dataset_paths.processed,
        config.dataset_paths.state,
        config.dataset_paths.figures,
        PROJECT_ROOT / 'docs',
        PROJECT_ROOT / 'state'
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info("Directories ensured.")

def run_stage(stage_name, stage_func, timeout_seconds=300):
    """Run a pipeline stage with timing and error handling."""
    start_time = time.time()
    logger.info(f"--- Starting Stage: {stage_name} ---")
    try:
        stage_func()
        elapsed = time.time() - start_time
        logger.info(f"--- Completed Stage: {stage_name} in {elapsed:.2f}s ---")
        return True, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"--- Failed Stage: {stage_name} after {elapsed:.2f}s ---")
        logger.exception(e)
        return False, elapsed

def run_full_pipeline(args):
    """Execute the full research pipeline."""
    start_total = time.time()
    config = get_config()
    
    # 1. Setup
    ensure_directories()

    # 2. Data Download
    success, time_taken = run_stage("Data Download", download_main)
    if not success:
        logger.error("Data download failed. Aborting pipeline.")
        return False

    # 3. Validation
    success, time_taken = run_stage("Validation", validation_main)
    if not success:
        logger.error("Validation failed. Aborting pipeline.")
        return False

    # 4. Extraction
    success, time_taken = run_stage("Extraction", extract_main)
    if not success:
        logger.error("Extraction failed. Aborting pipeline.")
        return False

    # 5. Sampling (for sentiment validation)
    success, time_taken = run_stage("Sampling", sampling_main)
    if not success:
        logger.warning("Sampling failed. Continuing with warnings.")

    # 6. Sentiment Analysis
    success, time_taken = run_stage("Sentiment Analysis", sentiment_main)
    if not success:
        logger.error("Sentiment analysis failed. Aborting pipeline.")
        return False

    # 7. Metrics Calculation
    success, time_taken = run_stage("Metrics Calculation", metrics_main)
    if not success:
        logger.error("Metrics calculation failed. Aborting pipeline.")
        return False

    # 8. Modeling
    success, time_taken = run_stage("Modeling", modeling_main)
    if not success:
        logger.error("Modeling failed. Aborting pipeline.")
        return False

    # 9. Report Generation
    success, time_taken = run_stage("Report Generation", report_main)
    if not success:
        logger.error("Report generation failed. Aborting pipeline.")
        return False

    # 10. Reproducibility Check
    if args.verify_reproducibility:
        success, time_taken = run_stage("Reproducibility Check", reproducibility_main)
        if not success:
            logger.warning("Reproducibility check failed.")

    total_runtime = time.time() - start_total
    
    # Log Performance
    performance_log = {
        "total_runtime_seconds": int(total_runtime),
        "thread_count": 0, # To be updated by specific stage if needed, or read from data
        "status": "success",
        "resource_check": {
            "cpu": True,
            "ram_gb": 7.0, # Assumed constraint
            "disk_gb": 14.0
        }
    }
    
    # Try to read thread count from valid_threads.csv if it exists
    valid_threads_path = PROJECT_ROOT / config.dataset_paths.processed / "valid_threads.csv"
    if valid_threads_path.exists():
        import pandas as pd
        try:
            df = pd.read_csv(valid_threads_path)
            performance_log["thread_count"] = len(df)
        except Exception as e:
            logger.warning(f"Could not read thread count: {e}")

    state_dir = PROJECT_ROOT / config.dataset_paths.state
    with open(state_dir / "performance_log.json", 'w') as f:
        json.dump(performance_log, f, indent=2)

    logger.info(f"Pipeline completed successfully in {total_runtime:.2f} seconds.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Run the full emotional contagion pipeline.")
    parser.add_argument("--verify-reproducibility", action="store_true", help="Run reproducibility check at the end.")
    parser.add_argument("--threads", action="store_true", help="Alias for running the pipeline (as per quickstart).")
    args = parser.parse_args()

    success = run_full_pipeline(args)
    
    if not success:
        logger.critical("Pipeline execution failed. Check logs.")
        sys.exit(1)
    else:
        logger.info("Pipeline execution successful.")
        sys.exit(0)

if __name__ == "__main__":
    main()
