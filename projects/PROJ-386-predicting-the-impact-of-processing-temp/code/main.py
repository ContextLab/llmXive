"""
Main orchestration entry point for the llmXive pipeline.

Responsibilities:
1. Verify runner environment (OS, CPU count, no GPU).
2. Enforce a hard timeout (GITHUB_ACTIONS_TIMEOUT) using signal.alarm.
3. Execute the pipeline stages sequentially.
"""
import os
import sys
import signal
import argparse
import logging
import time
from datetime import timedelta

# Import config for paths and timeout settings
from config import GITHUB_ACTIONS_TIMEOUT
from config import ensure_dirs
from config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Timeout handler
def timeout_handler(signum, frame):
    raise TimeoutError(f"Pipeline execution exceeded the hard limit of {GITHUB_ACTIONS_TIMEOUT} seconds.")

def verify_runner_environment():
    """
    Verifies the execution environment matches requirements:
    - OS: Linux (ubuntu-latest)
    - GPU: None
    - CPU: Count available
    """
    logger.info("Verifying runner environment...")
    
    # Check OS
    if sys.platform != 'linux':
        logger.warning(f"Running on non-Linux platform: {sys.platform}. Expected 'linux' (ubuntu-latest).")
        # Not a hard fail, but a warning for CI context
    
    # Check GPU availability (basic check)
    try:
        import torch
        if torch.cuda.is_available():
            logger.warning("GPU detected. Running on CPU as per project constraints.")
        else:
            logger.info("No GPU detected. Running on CPU.")
    except ImportError:
        logger.info("PyTorch not installed. Skipping GPU check.")
    
    # CPU Count
    cpu_count = os.cpu_count()
    logger.info(f"Detected CPU count: {cpu_count}")
    
    if cpu_count < 2:
        logger.warning("Low CPU count detected. Performance may be impacted.")
    
    return True

def run_pipeline():
    """
    Executes the pipeline stages.
    Orchestrates the execution of data ingestion, preprocessing, and modeling.
    """
    logger.info("Starting pipeline execution...")
    
    # Ensure directories exist
    ensure_dirs()
    
    # Stage 1: Data Ingestion
    # Uses the main entry point from data.ingestion
    ingestion_script = os.path.join(os.path.dirname(__file__), 'data', 'ingestion.py')
    if os.path.exists(ingestion_script):
        logger.info("Data ingestion module found. Executing...")
        # Import and run the ingestion pipeline
        from data.ingestion import main as ingestion_main
        # We pass a small sample size for quick verification if needed, 
        # but the script handles its own args.
        # To avoid arg conflicts, we temporarily replace sys.argv
        original_argv = sys.argv
        sys.argv = [ingestion_script] # Run with default args
        try:
            ingestion_main()
        except SystemExit as e:
            if e.code != 0:
                raise RuntimeError(f"Data ingestion failed with exit code {e.code}")
        finally:
            sys.argv = original_argv
        logger.info("Data ingestion stage complete.")
    else:
        raise FileNotFoundError("Data ingestion module (code/data/ingestion.py) not found.")

    # Stage 2: Preprocessing
    preprocessing_script = os.path.join(os.path.dirname(__file__), 'data', 'preprocessing.py')
    if os.path.exists(preprocessing_script):
        logger.info("Preprocessing module found. Executing...")
        from data.preprocessing import main as preprocessing_main
        original_argv = sys.argv
        sys.argv = [preprocessing_script]
        try:
            preprocessing_main()
        except SystemExit as e:
            if e.code != 0:
                raise RuntimeError(f"Preprocessing failed with exit code {e.code}")
        finally:
            sys.argv = original_argv
        logger.info("Preprocessing stage complete.")
    else:
        raise FileNotFoundError("Preprocessing module (code/data/preprocessing.py) not found.")

    # Stage 3: Baseline Modeling
    baseline_script = os.path.join(os.path.dirname(__file__), 'modeling', 'baseline.py')
    if os.path.exists(baseline_script):
        logger.info("Baseline modeling module found. Executing...")
        from modeling.baseline import main as baseline_main
        original_argv = sys.argv
        sys.argv = [baseline_script]
        try:
            baseline_main()
        except SystemExit as e:
            if e.code != 0:
                raise RuntimeError(f"Baseline modeling failed with exit code {e.code}")
        finally:
            sys.argv = original_argv
        logger.info("Baseline modeling stage complete.")
    else:
        raise FileNotFoundError("Baseline modeling module (code/modeling/baseline.py) not found.")

    # Stage 4: RF Modeling & Analysis
    rf_script = os.path.join(os.path.dirname(__file__), 'modeling', 'rf_model.py')
    if os.path.exists(rf_script):
        logger.info("Random Forest modeling module found. Executing...")
        from modeling.rf_model import main as rf_main
        original_argv = sys.argv
        sys.argv = [rf_script]
        try:
            rf_main()
        except SystemExit as e:
            if e.code != 0:
                raise RuntimeError(f"RF modeling failed with exit code {e.code}")
        finally:
            sys.argv = original_argv
        logger.info("RF modeling stage complete.")
    else:
        raise FileNotFoundError("Random Forest modeling module (code/modeling/rf_model.py) not found.")

    logger.info("Pipeline execution finished successfully.")

def main():
    parser = argparse.ArgumentParser(description="Orchestration entry point for llmXive pipeline.")
    parser.add_argument('--timeout', type=int, default=GITHUB_ACTIONS_TIMEOUT,
                        help=f"Timeout in seconds (default: {GITHUB_ACTIONS_TIMEOUT})")
    args = parser.parse_args()

    # Set the hard timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(args.timeout)
    
    logger.info(f"Hard timeout set to {args.timeout} seconds ({timedelta(seconds=args.timeout)}).")

    try:
        verify_runner_environment()
        run_pipeline()
    except TimeoutError as e:
        logger.error(f"CRITICAL: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}")
        sys.exit(1)
    finally:
        # Cancel the alarm
        signal.alarm(0)

if __name__ == "__main__":
    main()
