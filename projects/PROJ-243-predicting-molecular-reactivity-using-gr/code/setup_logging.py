"""
Script to initialize the logging infrastructure for the project.

This script ensures that the logging directories exist and the
logging utility is properly configured.
"""
import sys
import os
from datetime import datetime
from utils.logging_utils import setup_logging, log_metric, flush_metrics
from config import ensure_directories

def main():
    """
    Main entry point for setup_logging.
    """
    # Ensure directories exist
    ensure_directories()
    
    # Setup logging
    logger = setup_logging(run_id="init")
    logger.info("Logging infrastructure setup started.")
    
    # Log initialization metric
    log_metric("logging_setup", "initialized", tags={"status": "success"})
    flush_metrics()
    
    logger.info("Logging infrastructure setup completed successfully.")
    print("Logging setup complete. Logs will be written to artifacts/logs/ and metrics to artifacts/metrics.json")

if __name__ == "__main__":
    main()