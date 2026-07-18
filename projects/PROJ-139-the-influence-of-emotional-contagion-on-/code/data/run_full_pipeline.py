import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import get_config, DatasetPaths
from data.download import download_data, main as main_download
from data.validation import run_validation_pipeline, main as main_validation
from data.extract import run_extraction, main as main_extract
from data.sentiment import main as main_sentiment
from data.metrics import run_decision_quality_pipeline, main as main_metrics
from data.modeling import run_modeling_pipeline, main as main_modeling
from data.sampling import main as main_sampling
from data.calculate_reliability import main as main_reliability
from data.sentiment_validation import main as main_sentiment_validation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'state' / 'pipeline_execution.log')
    ]
)
logger = logging.getLogger(__name__)

CONFIG = get_config()
PATHS = CONFIG.paths

def ensure_directories():
    """Ensure all required output directories exist."""
    dirs = [
        PATHS.raw,
        PATHS.processed,
        PATHS.state,
        PATHS.figures,
        PATHS.logs
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info("Ensured all output directories exist.")

def run_stage(name, func, *args, **kwargs):
    """Run a pipeline stage with timing and error handling."""
    logger.info(f"--- Starting Stage: {name} ---")
    start = time.time()
    try:
        result = func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"--- Completed Stage: {name} in {duration:.2f}s ---")
        return True, duration, result
    except Exception as e:
        duration = time.time() - start
        logger.error(f"--- Failed Stage: {name} after {duration:.2f}s ---")
        logger.error(f"Error: {str(e)}")
        return False, duration, str(e)

def run_full_pipeline(thread_limit: int = 500):
    """
    Execute the full research pipeline on N threads.
    Returns a performance log dictionary.
    """
    start_time = time.time()
    performance_log = {
        "start_time": datetime.utcnow().isoformat(),
        "thread_limit": thread_limit,
        "stages": [],
        "total_runtime_seconds": 0,
        "status": "success",
        "error_details": None
    }

    ensure_directories()

    # Define pipeline stages
    # Note: We pass the thread_limit to the download/extraction logic where possible
    # or rely on the underlying scripts to handle sampling if implemented there.
    # Since the existing API surface doesn't explicitly take a limit in main(),
    # we assume the underlying scripts process available data or we rely on
    # the data already present/limited by previous steps.
    
    stages = [
        ("Data Download", lambda: download_data(limit=thread_limit)),
        ("Ground Truth Validation", lambda: run_validation_pipeline()),
        ("Thread Extraction", lambda: run_extraction()),
        ("Sentiment Analysis", lambda: apply_vader_sentiment()), # Wrapper needed
        ("Sentiment Validation Pipeline", lambda: main_sampling() and main_reliability() and main_sentiment_validation()),
        ("Decision Quality Metrics", lambda: run_decision_quality_pipeline()),
        ("Statistical Modeling", lambda: run_modeling_pipeline()),
    ]

    # Wrap specific functions if they aren't directly callable as pipelines
    def apply_vader_sentiment():
        # The main function in sentiment.py handles the full dataset
        # We rely on the fact that previous steps filtered the data
        from data.sentiment import main as sentiment_main
        sentiment_main()

    # Execute stages
    for stage_name, stage_func in stages:
        success, duration, result = run_stage(stage_name, stage_func)
        performance_log["stages"].append({
            "name": stage_name,
            "success": success,
            "duration_seconds": duration,
            "result_summary": str(result)[:200] if result else None
        })
        
        if not success:
            performance_log["status"] = "failure"
            performance_log["error_details"] = result
            break

    total_runtime = time.time() - start_time
    performance_log["total_runtime_seconds"] = total_runtime
    performance_log["end_time"] = datetime.utcnow().isoformat()

    # Check SC-005: 6-hour limit
    six_hours_seconds = 6 * 3600
    if total_runtime > six_hours_seconds:
        performance_log["status"] = "failure"
        performance_log["error_details"] = f"Runtime exceeded 6 hours ({total_runtime:.2f}s > {six_hours_seconds}s)"
        logger.critical(f"Pipeline exceeded 6-hour limit. Status: {performance_log['status']}")
    else:
        logger.info(f"Pipeline completed successfully in {total_runtime:.2f}s (Limit: {six_hours_seconds}s)")

    # Write performance log
    log_path = PATHS.state / "performance_log.json"
    with open(log_path, 'w') as f:
        json.dump(performance_log, f, indent=2)
    
    logger.info(f"Performance log written to {log_path}")
    return performance_log

def main():
    """Entry point for the full pipeline runner."""
    logger.info("Starting Full Pipeline Execution (T025)")
    try:
        result = run_full_pipeline(thread_limit=500)
        if result["status"] == "failure":
            logger.error("Pipeline execution failed.")
            sys.exit(1)
        else:
            logger.info("Pipeline execution completed successfully.")
            sys.exit(0)
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
