"""
Orchestration entry point for the llmXive automated science pipeline.
Implements hard timeout enforcement and runner verification.
"""
import os
import sys
import signal
import argparse
import logging
import time
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global timeout flag
timeout_occurred = False

def timeout_handler(signum, frame):
    """Signal handler for timeout enforcement."""
    global timeout_occurred
    timeout_occurred = True
    logger.error("Hard timeout triggered. Aborting pipeline execution.")
    # Raise an exception to break out of any long-running loops
    raise TimeoutError("Pipeline execution exceeded the hard timeout limit.")

def verify_runner_environment():
    """
    Verify the runner environment matches expected constraints.
    Checks for ubuntu-latest, no GPU, and CPU count.
    """
    logger.info("Verifying runner environment...")
    
    # Check OS (GitHub Actions ubuntu-latest runs on Linux)
    if sys.platform != 'linux':
        logger.warning(f"Running on non-Linux platform: {sys.platform}. Expected Linux.")
    
    # Check for GPU availability (we expect CPU-only)
    try:
        import torch
        if torch.cuda.is_available():
            logger.warning("GPU detected. Pipeline is configured for CPU-only execution.")
            # Note: We don't abort, just warn, as the pipeline should still work on CPU
        else:
            logger.info("No GPU detected. Running in CPU-only mode as expected.")
    except ImportError:
        logger.info("PyTorch not installed. Assuming CPU-only environment.")
    
    # Check CPU count
    cpu_count = os.cpu_count()
    logger.info(f"Detected {cpu_count} CPU cores.")
    
    # Verify GitHub Actions environment variables if present
    if 'GITHUB_ACTIONS' in os.environ and os.environ['GITHUB_ACTIONS'] == 'true':
        logger.info("Running in GitHub Actions environment.")
        runner_os = os.environ.get('RUNNER_OS', 'Unknown')
        logger.info(f"Runner OS: {runner_os}")
        
        # Verify it's ubuntu-latest (usually implies Ubuntu 22.04 or similar)
        if runner_os != 'Linux':
            logger.warning(f"Expected Linux runner, got {runner_os}")
    
    logger.info("Runner environment verification complete.")
    return True

def run_pipeline(args):
    """
    Execute the full pipeline with timeout enforcement.
    """
    global timeout_occurred
    
    # Set up signal handler for timeout
    if args.timeout > 0:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(args.timeout)
        logger.info(f"Hard timeout set to {args.timeout} seconds.")
    else:
        logger.warning("No timeout set. Pipeline will run indefinitely.")
    
    start_time = time.time()
    
    try:
        logger.info("Starting pipeline execution...")
        
        # 1. Verify Runner Environment
        verify_runner_environment()
        
        # 2. Ingestion Pipeline (Data Download & Validation)
        logger.info("Step 1: Ingestion Pipeline")
        from data.ingestion import run_pipeline as run_ingestion_pipeline
        run_ingestion_pipeline(args.urls, args.output, args.stats)
        
        if timeout_occurred:
            raise TimeoutError("Timeout during ingestion pipeline.")
        
        # 3. Preprocessing Pipeline
        logger.info("Step 2: Preprocessing Pipeline")
        from data.preprocessing import run_preprocessing_pipeline
        # Assuming processed data output is handled internally by the pipeline
        run_preprocessing_pipeline(
            input_path=args.output if args.output else 'data/raw/ingested_data.csv',
            output_path='data/processed/processed_data.csv'
        )
        
        if timeout_occurred:
            raise TimeoutError("Timeout during preprocessing pipeline.")
        
        # 4. Baseline Modeling
        logger.info("Step 3: Baseline Modeling")
        from modeling.baseline import run_baseline_pipeline
        run_baseline_pipeline(
            data_path='data/processed/processed_data.csv',
            output_path='data/artifacts/baseline_model.pkl'
        )
        
        if timeout_occurred:
            raise TimeoutError("Timeout during baseline modeling.")
        
        # 5. Random Forest Modeling
        logger.info("Step 4: Random Forest Modeling")
        from modeling.rf_model import run_rf_pipeline
        run_rf_pipeline(
            data_path='data/processed/processed_data.csv',
            baseline_model_path='data/artifacts/baseline_model.pkl',
            output_path='data/artifacts/rf_model.pkl'
        )
        
        if timeout_occurred:
            raise TimeoutError("Timeout during RF modeling.")
        
        # 6. Analysis & Reporting
        logger.info("Step 5: Analysis & Reporting")
        from analysis.reporting import run_reporting_pipeline
        run_reporting_pipeline(
            data_path='data/processed/processed_data.csv',
            baseline_model_path='data/artifacts/baseline_model.pkl',
            rf_model_path='data/artifacts/rf_model.pkl',
            output_dir='data/artifacts'
        )
        
        if timeout_occurred:
            raise TimeoutError("Timeout during reporting pipeline.")
        
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Pipeline completed successfully in {duration:.2f} seconds.")
        
    except TimeoutError as e:
        logger.error(f"Pipeline failed due to timeout: {e}")
        # Write timeout status
        timeout_status = {
            "status": "aborted",
            "reason": str(e),
            "elapsed_time": time.time() - start_time
        }
        with open('data/artifacts/timeout_status.json', 'w') as f:
            import json
            json.dump(timeout_status, f, indent=2)
        raise
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        raise
    finally:
        # Cancel the alarm if it was set
        if args.timeout > 0:
            signal.alarm(0)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Orchestration entry point for the science pipeline.')
    parser.add_argument('--urls', type=str, nargs='+', 
                      default=['https://archive.ics.uci.edu/ml/machine-learning-databases/00470/Aluminum_Alloy_Data.csv'],
                      help='URLs to download data from.')
    parser.add_argument('--output', type=str, default='data/raw/ingested_data.csv',
                      help='Output path for ingested data.')
    parser.add_argument('--stats', action='store_true',
                      help='Generate streaming statistics.')
    parser.add_argument('--sample-size', type=int, default=None,
                      help='Sample size for testing (optional).')
    parser.add_argument('--timeout', type=int, default=0,
                      help='Hard timeout in seconds (0 = no timeout).')
    
    args = parser.parse_args()
    
    # Set global seed if specified in config
    try:
        from config import set_global_seed
        set_global_seed(42)
    except ImportError:
        logger.warning("Config module not found. Skipping seed setting.")
    
    run_pipeline(args)

if __name__ == '__main__':
    main()
