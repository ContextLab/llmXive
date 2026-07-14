"""
Script to initialize the logging infrastructure.

This script ensures that the logging configuration is set up
and the necessary directories exist.
"""
import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging_utils import setup_logging, log_metric, flush_metrics
from config import ensure_directories

def main():
    """Initialize logging infrastructure."""
    print("Initializing logging infrastructure...")
    
    ensure_directories()
    logger = setup_logging()
    
    logger.info("Logging infrastructure initialized successfully")
    logger.info(f"Log file location: {os.path.join(logger.handlers[0].baseFilename)}")
    
    log_metric("logging_setup", 1.0, {"status": "success", "timestamp": datetime.now().isoformat()})
    flush_metrics()
    
    print("Logging infrastructure ready. Check artifacts/logs/ for log files.")
    print("Metrics will be written to artifacts/metrics.json")

if __name__ == "__main__":
    main()