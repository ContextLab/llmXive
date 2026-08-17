"""
Setup script for logging infrastructure.
Initializes logging directories and configuration.
"""
import sys
import os
from datetime import datetime
from utils.logging_utils import setup_logging, log_metric, flush_metrics
from config import ensure_directories, get_config

def setup_script_logging() -> None:
    """
    Initialize the logging infrastructure for the project.
    Creates necessary directories and configures loggers.
    """
    # Ensure all required directories exist
    ensure_directories()
    
    # Setup logging
    logger = setup_logging()
    
    logger.info("Logging infrastructure initialized")
    
    # Log initialization metrics
    log_metric("logging_initialized", True, run_id="setup")
    log_metric("timestamp", datetime.now().isoformat(), run_id="setup")
    
    flush_metrics()

def main():
    """
    Main entry point for logging setup script.
    """
    try:
        setup_script_logging()
        print("Logging infrastructure setup completed successfully.")
        return 0
    except Exception as e:
        print(f"Error setting up logging: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
