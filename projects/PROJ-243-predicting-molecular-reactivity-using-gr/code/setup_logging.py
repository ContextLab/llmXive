"""
Setup script for logging infrastructure (Task T009).

This script initializes the logging directories and verifies
that the logging utilities are functional.
"""
import sys
import os
from datetime import datetime
from utils.logging_utils import setup_logging, log_metric, flush_metrics, log_execution_summary
from config import ensure_directories, get_config

def setup_script_logging() -> None:
    """
    Initialize logging for the setup script itself.
    """
    # Ensure required directories exist
    ensure_directories([
        "artifacts/logs",
        "artifacts/metrics"
    ])
    
    # Initialize the main logging infrastructure
    logger = setup_logging()
    logger.info("Starting logging infrastructure setup (T009)...")

def main() -> None:
    """
    Main entry point for T009.
    
    This script:
    1. Creates necessary directories.
    2. Initializes the logging system.
    3. Writes a test log entry to verify functionality.
    4. Logs an initial metric to `artifacts/metrics.json`.
    """
    start_time = datetime.now()
    
    # Setup logging for this script
    setup_script_logging()
    logger = setup_logging()
    
    try:
        # Verify directories
        dirs = ["artifacts/logs", "artifacts/metrics"]
        for d in dirs:
            if not os.path.exists(d):
                os.makedirs(d)
                logger.info(f"Created directory: {d}")
            else:
                logger.info(f"Directory exists: {d}")
        
        # Log a startup metric
        log_metric("pipeline_start", datetime.now().isoformat())
        log_metric("task_id", "T009")
        
        # Log execution summary for this setup run
        duration = (datetime.now() - start_time).total_seconds()
        log_execution_summary(
            task_id="T009",
            success=True,
            duration_seconds=duration,
            message="Logging infrastructure initialized successfully."
        )
        
        logger.info("Logging infrastructure setup complete.")
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        log_execution_summary(
            task_id="T009",
            success=False,
            duration_seconds=duration,
            message=f"Failed to setup logging: {str(e)}"
        )
        logger.error(f"Setup failed: {str(e)}")
        sys.exit(1)
    finally:
        flush_metrics()

if __name__ == "__main__":
    main()