import logging
import sys
import os
import time
import resource
from pathlib import Path
from typing import Optional, Dict, Any

from config_utils import load_config, set_random_seed, setup_environment
from download import main as run_download
from preprocess import main as run_preprocessing
from metrics import main as run_metrics
from analysis import main as run_analysis
from report import main as run_report_generation
from quickstart_validator import verify_outputs

# Constants for runtime constraints
RUNTIME_TARGET_SECONDS = 4 * 3600  # 4 hours in seconds
MEMORY_TARGET_BYTES = 4 * 1024**3   # 4 GB in bytes

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Configure logging for the pipeline."""
    logger = logging.getLogger("llmXive_pipeline")
    logger.setLevel(level)

    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger

def get_memory_usage_bytes() -> int:
    """Get current memory usage in bytes (Linux/Unix only)."""
    if sys.platform == 'win32':
        # Fallback for Windows if resource module not available
        return 0
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in kilobytes on Linux
    return usage.ru_maxrss * 1024

def profile_memory_usage(logger: logging.Logger) -> Dict[str, int]:
    """Profile memory usage at a checkpoint."""
    current_mem = get_memory_usage_bytes()
    logger.info(f"Current memory usage: {current_mem / (1024**2):.2f} MB")
    return {"current_memory_bytes": current_mem}

def verify_runtime_target(start_time: float, logger: logging.Logger) -> bool:
    """Verify that the runtime is within the 4-hour target."""
    elapsed = time.time() - start_time
    elapsed_hours = elapsed / 3600
    target_hours = RUNTIME_TARGET_SECONDS / 3600

    logger.info(f"Runtime verification: Elapsed time = {elapsed:.2f} seconds ({elapsed_hours:.2f} hours)")
    logger.info(f"Target runtime: < {target_hours:.2f} hours ({RUNTIME_TARGET_SECONDS} seconds)")

    if elapsed > RUNTIME_TARGET_SECONDS:
        logger.error(f"Runtime target exceeded! Elapsed: {elapsed_hours:.2f}h > Target: {target_hours:.2f}h")
        return False
    else:
        logger.info(f"Runtime target met: {elapsed_hours:.2f}h < {target_hours:.2f}h")
        return True

def run_full_pipeline(config: Dict[str, Any], logger: logging.Logger) -> bool:
    """Execute the full research pipeline with runtime monitoring."""
    start_time = time.time()
    success = True

    try:
        logger.info("Starting Download Phase...")
        run_download()
        profile_memory_usage(logger)

        logger.info("Starting Preprocessing Phase...")
        run_preprocessing()
        profile_memory_usage(logger)

        logger.info("Starting Metrics Computation Phase...")
        run_metrics()
        profile_memory_usage(logger)

        logger.info("Starting Analysis Phase...")
        run_analysis()
        profile_memory_usage(logger)

        logger.info("Starting Report Generation Phase...")
        run_report_generation()
        profile_memory_usage(logger)

        logger.info("Verifying outputs...")
        verify_outputs()

    except Exception as e:
        logger.error(f"Pipeline failed with error: {str(e)}", exc_info=True)
        success = False
    finally:
        # Final runtime verification
        if not verify_runtime_target(start_time, logger):
            success = False

        total_mem = get_memory_usage_bytes()
        logger.info(f"Pipeline finished. Total runtime: {time.time() - start_time:.2f}s, Final Memory: {total_mem / (1024**2):.2f} MB")

    return success

def main():
    """Entry point for the main pipeline."""
    # Load configuration
    config_path = Path("code/config.yaml")
    config = load_config(config_path)

    # Setup environment and logging
    setup_environment(config)
    log_file = "data/results/pipeline_run.log"
    logger = setup_logging(log_file=log_file)

    logger.info("Initializing llmXive Research Pipeline")
    logger.info(f"Runtime Target: < {RUNTIME_TARGET_SECONDS / 3600:.2f} hours")
    logger.info(f"Memory Target: < {MEMORY_TARGET_BYTES / (1024**3):.2f} GB")

    # Run the pipeline
    success = run_full_pipeline(config, logger)

    if success:
        logger.info("Pipeline completed successfully within targets.")
        sys.exit(0)
    else:
        logger.error("Pipeline execution failed or exceeded targets.")
        sys.exit(1)

if __name__ == "__main__":
    main()