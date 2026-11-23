import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path

# Import the main pipeline orchestrator
from main import run_pipeline

# Ensure we are in the project root context
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"
LOG_DIR = PROJECT_ROOT / "logs"

# Configure logging for the timing script
def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = LOG_DIR / "timing_run.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def ensure_dirs():
    """Ensure all necessary directories exist."""
    logging.info("Ensuring required directories exist...")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    # Ensure data directories exist if they don't (setup task usually handles this)
    (PROJECT_ROOT / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "data" / "derived").mkdir(parents=True, exist_ok=True)

def run_timed_pipeline(logger):
    """
    Executes the full pipeline while measuring execution time.
    Returns a dict with timing metrics.
    """
    logger.info("Starting full pipeline execution with timing instrumentation...")
    start_time = time.time()
    start_dt = datetime.now()

    try:
        # Run the main pipeline logic
        # run_pipeline() is expected to orchestrate download, preprocess, model, viz, robustness
        run_pipeline()
        status = "success"
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        status = "failed"
        raise
    finally:
        end_time = time.time()
        end_dt = datetime.now()

    duration_seconds = end_time - start_time
    
    metrics = {
        "start_time_iso": start_dt.isoformat(),
        "end_time_iso": end_dt.isoformat(),
        "duration_seconds": duration_seconds,
        "duration_minutes": duration_seconds / 60,
        "status": status,
        "limit_hours": 6.0,
        "limit_seconds": 6 * 3600,
        "within_limit": duration_seconds <= (6 * 3600)
    }
    
    logger.info(f"Pipeline finished. Status: {status}, Duration: {metrics['duration_seconds']:.2f}s")
    return metrics

def save_timing_report(metrics, logger):
    """Saves the timing metrics to results/timing_report.json."""
    output_path = RESULTS_DIR / "timing_report.json"
    logger.info(f"Saving timing report to {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info("Timing report saved successfully.")
    return output_path

def main():
    logger = setup_logging()
    ensure_dirs()
    
    try:
        metrics = run_timed_pipeline(logger)
        save_timing_report(metrics, logger)
        
        if not metrics["within_limit"]:
            logger.warning(f"Pipeline exceeded 6-hour limit! Duration: {metrics['duration_seconds']}s")
            sys.exit(1)
        else:
            logger.info("Pipeline completed within the 6-hour CPU limit.")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Critical error during timed execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
