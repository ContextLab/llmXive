"""
Setup script for logging infrastructure.

Initializes the logging system and creates necessary directories.
"""
import sys
import os
from datetime import datetime
from utils.logging_utils import setup_logging, log_metric, flush_metrics, log_execution_summary
from config import ensure_directories, get_config

def setup_script_logging():
    """
    Setup logging for the script itself.
    
    Returns:
        Configured logger instance.
    """
    config = get_config()
    log_dir = os.path.join(config.get("artifacts_dir", "artifacts"), "logs")
    
    # Ensure directories exist
    ensure_directories([log_dir])
    
    logger = setup_logging(
        logger_name="setup_logging",
        log_dir=log_dir,
        log_level=logging.INFO,
        console_output=True
    )
    
    logger.info("Logging infrastructure setup started.")
    return logger

def main():
    """
    Main entry point for the logging setup script.
    
    This script:
    1. Ensures the artifacts/logs directory exists.
    2. Initializes the logging system.
    3. Writes an initial metrics entry.
    4. Logs a test execution summary.
    """
    logger = setup_script_logging()
    
    try:
        config = get_config()
        artifacts_dir = config.get("artifacts_dir", "artifacts")
        metrics_file = os.path.join(artifacts_dir, "metrics.json")
        log_dir = os.path.join(artifacts_dir, "logs")
        
        # Ensure directories exist
        ensure_directories([log_dir, artifacts_dir])
        
        logger.info(f"Directories ensured: {log_dir}, {artifacts_dir}")
        
        # Log initial metric
        log_metric(
            "logging_setup_completed",
            True,
            metadata={
                "timestamp": datetime.utcnow().isoformat(),
                "log_dir": log_dir,
                "metrics_file": metrics_file
            },
            metrics_file=metrics_file
        )
        
        logger.info(f"Initial metric logged to {metrics_file}")
        
        # Log execution summary
        log_execution_summary(
            task_id="T009",
            status="success",
            duration_seconds=0.1,
            metrics={
                "log_directory_created": True,
                "metrics_file_created": os.path.exists(metrics_file)
            },
            log_dir=log_dir
        )
        
        logger.info("Logging infrastructure setup completed successfully.")
        
        # Flush any pending writes
        flush_metrics(metrics_file)
        
        print(f"Logging infrastructure initialized.")
        print(f"Log directory: {log_dir}")
        print(f"Metrics file: {metrics_file}")
        
    except Exception as e:
        logger.error(f"Failed to setup logging infrastructure: {str(e)}", exc_info=True)
        log_execution_summary(
            task_id="T009",
            status="failed",
            duration_seconds=0.1,
            error_message=str(e),
            log_dir=log_dir
        )
        sys.exit(1)

if __name__ == "__main__":
    main()