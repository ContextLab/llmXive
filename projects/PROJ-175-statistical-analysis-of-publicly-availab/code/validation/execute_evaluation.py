"""
Execution Wrapper for T029.
Orchestrates the metrics calculation step.
"""
import os
import sys
import json
import time
import logging
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from evaluation.metrics import main as run_metrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(ROOT_DIR / "data" / "evaluation_log.json", mode='w')
    ]
)
logger = logging.getLogger(__name__)

def run_evaluation_step() -> bool:
    """
    Runs the metrics calculation step.
    Returns True if successful, False otherwise.
    """
    logger.info("Starting Evaluation Step (T029)")
    start_time = time.time()

    try:
        run_metrics()
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Evaluation Step completed successfully in {duration:.2f} seconds.")
        return True
    except Exception as e:
        logger.error(f"Evaluation Step failed: {e}", exc_info=True)
        end_time = time.time()
        duration = end_time - start_time
        
        # Log failure to the JSON log file
        log_entry = {
            "step": "T029_Metrics_Calculation",
            "status": "FAILED",
            "error": str(e),
            "duration_seconds": duration,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        log_file = ROOT_DIR / "data" / "evaluation_log.json"
        with open(log_file, "w") as f:
            json.dump(log_entry, f, indent=2)
        return False

def main():
    success = run_evaluation_step()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
