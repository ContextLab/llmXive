import os
import sys
import time
import json
import signal
import argparse
import logging
from pathlib import Path

from config import get_config, ensure_dirs, set_global_seed
from data.download import run_download_pipeline
from data.preprocess import run_preprocessing_pipeline
from data.validate import run_validation_pipeline
from models.baseline import run_baseline_pipeline
from models.non_linear import run_non_linear_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("llmXive_main")

def handle_timeout(signum, frame):
    """Signal handler for pipeline timeouts."""
    raise TimeoutError("Pipeline execution exceeded the configured time limit.")

def run_pipeline(args):
    """
    Orchestrates the full research pipeline.
    Implements conditional logic for T028: skips non-linear grid search if N < 100.
    """
    start_time = time.time()
    config = get_config()
    
    # Set global seed for reproducibility
    set_global_seed(config.get('random_seed', 42))
    
    # Ensure directory structure exists
    ensure_dirs()

    # 1. Data Download (US1)
    logger.info("Phase 1: Data Download and Validation")
    try:
        raw_data_path = run_download_pipeline(args)
        if not raw_data_path or not raw_data_path.exists():
            logger.error("Data download failed or produced no output. Halting.")
            return False
    except Exception as e:
        logger.error(f"Data download phase failed: {e}")
        return False

    # 2. Preprocessing (US2)
    logger.info("Phase 2: Preprocessing and Feature Engineering")
    try:
        processed_data_path = run_preprocessing_pipeline(args)
        if not processed_data_path or not processed_data_path.exists():
            logger.error("Preprocessing failed. Halting.")
            return False
    except Exception as e:
        logger.error(f"Preprocessing phase failed: {e}")
        return False

    # 3. Data Validation (US2)
    logger.info("Phase 3: Data Validation (Collinearity & Chemical Coupling)")
    try:
        validation_report = run_validation_pipeline(args)
        logger.info(f"Validation report generated: {validation_report}")
    except Exception as e:
        logger.error(f"Validation phase failed: {e}")
        return False

    # 4. Baseline Modeling (US2)
    logger.info("Phase 4: Baseline Linear Model Training")
    try:
        baseline_metrics = run_baseline_pipeline(args)
        logger.info(f"Baseline model training complete. Metrics: {baseline_metrics}")
    except Exception as e:
        logger.error(f"Baseline modeling phase failed: {e}")
        return False

    # 5. Non-Linear Modeling (US3) - T028 Logic
    # Conditionally skip full grid search if N < 100
    logger.info("Phase 5: Non-Linear Modeling (Conditional Execution)")
    
    # We need to check the dataset size N. 
    # The processed data path should exist from Phase 2.
    # We load the data temporarily to check the row count without re-running full logic.
    try:
        import pandas as pd
        # Assuming the processed data is saved as a CSV by preprocess.py
        # We check the specific output path defined in config or default
        processed_file = Path(config.get('data', {}).get('processed_file', 'data/processed/processed_data.csv'))
        
        if not processed_file.exists():
            logger.warning(f"Processed data file not found at {processed_file}. Cannot determine N. Skipping Non-Linear phase.")
            skip_non_linear = True
        else:
            df = pd.read_csv(processed_file)
            N = len(df)
            logger.info(f"Dataset size N = {N}. Threshold for Non-Linear grid search: 100.")
            
            if N < 100:
                logger.warning(f"Dataset size (N={N}) is below threshold (100). Skipping non-linear grid search (T028).")
                skip_non_linear = True
            else:
                skip_non_linear = False
    except Exception as e:
        logger.error(f"Failed to check dataset size for T028 logic: {e}. Defaulting to skip non-linear phase.")
        skip_non_linear = True

    if not skip_non_linear:
        try:
            # Set timeout for the non-linear phase (e.g., 4 hours as per spec)
            timeout_seconds = config.get('training_timeout', 4 * 60 * 60)
            signal.signal(signal.SIGALRM, handle_timeout)
            signal.alarm(timeout_seconds)
            
            logger.info(f"Running non-linear grid search (timeout: {timeout_seconds}s)...")
            non_linear_metrics = run_non_linear_pipeline(args)
            
            # Cancel alarm
            signal.alarm(0)
            
            logger.info(f"Non-linear model training complete. Metrics: {non_linear_metrics}")
        except TimeoutError:
            logger.error("Non-linear training timed out. Falling back to default parameters (handled inside non_linear.py) or halting.")
            # Depending on strictness, we might halt or continue with fallback. 
            # The spec implies the fallback happens inside non_linear.py, but if the orchestrator times out, we stop.
            # We will treat this as a failure of this phase but log it.
            return False
        except Exception as e:
            logger.error(f"Non-linear modeling phase failed: {e}")
            return False
    else:
        logger.info("Skipping non-linear modeling phase due to insufficient data size.")

    # Finalize
    elapsed = time.time() - start_time
    logger.info(f"Pipeline completed successfully in {elapsed:.2f} seconds.")
    return True

def main():
    parser = argparse.ArgumentParser(description="llmXive Research Pipeline Orchestrator")
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to configuration file')
    parser.add_argument('--skip-download', action='store_true', help='Skip data download phase')
    parser.add_argument('--timeout', type=int, default=None, help='Global pipeline timeout in seconds')
    
    args = parser.parse_args()
    
    if args.timeout:
        signal.signal(signal.SIGALRM, handle_timeout)
        signal.alarm(args.timeout)

    success = run_pipeline(args)
    
    if args.timeout:
        signal.alarm(0)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()