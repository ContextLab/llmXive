import sys
import os
from datetime import datetime
from utils.logging_utils import setup_logging, log_metric, flush_metrics
from config import ensure_directories

def main():
    """
    Initializes the logging infrastructure.
    This script ensures that the directories exist and the logging system is ready.
    It also writes a startup entry to the metrics.json file.
    """
    ensure_directories()
    
    # Initialize the logger for this setup script
    logger = setup_logging("setup_logging")
    logger.info("Starting logging infrastructure setup.")
    
    # Log a startup metric
    log_metric("system_startup", datetime.now().isoformat())
    log_metric("logging_initialized", True)
    
    logger.info("Logging infrastructure ready. Check artifacts/logs/ for logs and artifacts/metrics.json for metrics.")
    
    flush_metrics()

if __name__ == "__main__":
    main()
