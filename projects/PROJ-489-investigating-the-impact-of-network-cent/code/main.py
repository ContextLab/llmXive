import logging
import sys
import os
import time
import resource
from pathlib import Path
from typing import Optional, Dict, Any
import json

# Import from sibling modules as per API surface
from config_utils import load_config, set_random_seed, setup_environment
from download import main as run_download
from preprocess import main as run_preprocessing
from metrics import main as run_metrics
from analysis import main as run_analysis
from report import main as run_report_generation
from quickstart_validator import verify_outputs

# Constants for runtime target
RUNTIME_TARGET_SECONDS = 4 * 60 * 60  # 4 hours in seconds

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure logging for the pipeline.
    Logs to both console and file if provided.
    """
    logger = logging.getLogger("llmXive_pipeline")
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def get_memory_usage_bytes() -> int:
    """
    Get current memory usage in bytes using resource module.
    Returns 0 if not supported (e.g., Windows without specific setup).
    """
    try:
        # ru_maxrss is in KB on Linux/macOS
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    except AttributeError:
        return 0

def profile_memory_usage(logger: logging.Logger) -> Dict[str, Any]:
    """
    Profile memory usage at a specific point in execution.
    """
    current_mem = get_memory_usage_bytes()
    mem_mb = current_mem / (1024 * 1024)
    logger.info(f"Current memory usage: {mem_mb:.2f} MB")
    return {"current_bytes": current_mem, "current_mb": mem_mb}

def verify_runtime_target(start_time: float, logger: logging.Logger) -> bool:
    """
    Verify that the elapsed runtime is within the 4-hour target (SC-002).
    Returns True if within target, False otherwise.
    """
    elapsed = time.time() - start_time
    elapsed_hours = elapsed / 3600
    elapsed_formatted = time.strftime("%H:%M:%S", time.gmtime(elapsed))
    target_formatted = time.strftime("%H:%M:%S", time.gmtime(RUNTIME_TARGET_SECONDS))

    logger.info(f"Runtime Check: Elapsed {elapsed_formatted} / Target {target_formatted}")

    if elapsed > RUNTIME_TARGET_SECONDS:
        logger.error(f"Runtime Target Exceeded: {elapsed_hours:.2f} hours > 4.0 hours limit.")
        return False
    else:
        logger.info(f"Runtime Target Met: Execution completed within {elapsed_hours:.2f} hours.")
        return True

def run_full_pipeline(config_path: Optional[str] = None, log_file: Optional[str] = None) -> bool:
    """
    Execute the full research pipeline with runtime logging and verification.
    Returns True if successful and within runtime limits, False otherwise.
    """
    start_time = time.time()
    logger = setup_logging(log_file)
    logger.info("Starting llmXive Pipeline Execution...")
    
    # Memory profile at start
    profile_memory_usage(logger)

    try:
        # Load configuration
        if config_path is None:
            config_path = "code/config.yaml"
        config = load_config(config_path)
        set_random_seed(config.get("random_seed", 42))
        setup_environment(config)

        logger.info("Phase 1: Downloading Data")
        run_download()

        logger.info("Phase 2: Preprocessing Data")
        run_preprocessing()

        logger.info("Phase 3: Computing Metrics")
        run_metrics()

        logger.info("Phase 4: Statistical Analysis")
        run_analysis()

        logger.info("Phase 5: Report Generation")
        run_report_generation()

        logger.info("Phase 6: Verification")
        verify_outputs()

    except Exception as e:
        logger.error(f"Pipeline failed with exception: {str(e)}", exc_info=True)
        return False

    # Final Runtime Verification (SC-002)
    success = verify_runtime_target(start_time, logger)
    
    if success:
        logger.info("Pipeline completed successfully within runtime constraints.")
        # Profile final memory
        profile_memory_usage(logger)
        return True
    else:
        logger.error("Pipeline completed but exceeded runtime constraints.")
        return False

def main():
    """
    Entry point for the pipeline.
    """
    # Default paths
    config_path = os.environ.get("LLMXIVE_CONFIG", "code/config.yaml")
    log_file = os.environ.get("LLMXIVE_LOG", "data/results/pipeline_execution.log")

    success = run_full_pipeline(config_path=config_path, log_file=log_file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()