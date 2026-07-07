import os
import sys
import time
import signal
import logging
import json
import yaml

from utils.timing_logger import timing_logger

# Import existing modules
from data.preprocess import main as run_preprocess
from data.generate_validation_report import main as run_validation_report
from models.baseline_nn import main as run_baseline
from models.deep_ensemble import main as run_ensemble
from models.mc_dropout import main as run_mc_dropout
from models.sparse_gp import main as run_sparse_gp

# Configuration
CONFIG_PATH = "code/config.yaml"
LOG_DIR = "logs"
PIPELINE_LOG = os.path.join(LOG_DIR, "pipeline.log")
os.makedirs(LOG_DIR, exist_ok=True)

# Global timeout
TIMEOUT_HOURS = 5.0
TIMEOUT_SECONDS = TIMEOUT_HOURS * 3600

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Pipeline exceeded 5-hour timeout.")

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(PIPELINE_LOG),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def run_pipeline(logger):
    logger.info("Starting UQ Pipeline...")
    
    # 1. Data Preprocessing (if not already done, but orchestrator calls it)
    # Note: T006 handles this, but we ensure it runs in the chain if needed.
    # For this task, we assume data is ready or run the script to ensure it.
    logger.info("Step 1: Preprocessing Data")
    timing_logger.start("preprocessing")
    try:
        # Assuming run_preprocess handles its own logging, we just time the block
        # In a real scenario, we might import functions instead of main() to control flow better
        # But per constraints, we call main() if that's the entry point.
        # We'll wrap the call to ensure timing capture.
        run_preprocess() 
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        return False
    timing_logger.stop("preprocessing")

    # 2. Baseline Training
    logger.info("Step 2: Training Baseline NN")
    timing_logger.start("baseline_training")
    run_baseline()
    timing_logger.stop("baseline_training")

    # 3. Deep Ensemble
    logger.info("Step 3: Training Deep Ensemble")
    timing_logger.start("ensemble_training")
    run_ensemble()
    timing_logger.stop("ensemble_training")

    # 4. MC Dropout
    logger.info("Step 4: Training MC Dropout")
    timing_logger.start("mc_dropout_training")
    run_mc_dropout()
    timing_logger.stop("mc_dropout_training")

    # 5. Sparse GP
    logger.info("Step 5: Training Sparse GP")
    timing_logger.start("sparse_gp_training")
    run_sparse_gp()
    timing_logger.stop("sparse_gp_training")

    # Save the final timing report
    timing_logger.save_report()
    
    # Calculate total time
    total_time = timing_logger.get_total_time()
    logger.info(f"Pipeline completed. Total training/inference time: {total_time:.2f}s")
    
    if total_time > TIMEOUT_SECONDS:
        logger.warning(f"Pipeline exceeded timeout budget ({total_time:.2f}s > {TIMEOUT_SECONDS}s)")
    
    return True

def main():
    logger = setup_logging()
    
    # Set up timeout signal
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(TIMEOUT_SECONDS))

    try:
        success = run_pipeline(logger)
        if success:
            logger.info("Pipeline finished successfully.")
            sys.exit(0)
        else:
            logger.error("Pipeline failed.")
            sys.exit(1)
    except TimeoutError as e:
        logger.error(f"TIMEOUT: {e}")
        sys.exit(1)
    finally:
        signal.alarm(0) # Disable alarm

if __name__ == "__main__":
    main()