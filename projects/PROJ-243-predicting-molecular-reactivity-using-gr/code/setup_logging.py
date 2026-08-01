import sys
import os
from datetime import datetime
from utils.logging_utils import setup_logging, log_metric, flush_metrics
from config import ensure_directories

def main():
    """
    Initialize the logging infrastructure for the project.
    This script ensures that the required directories exist and
    configures the global logger to write to artifacts/logs and artifacts/metrics.json.
    """
    # Ensure standard directories exist as per project setup
    ensure_directories()
    
    # Initialize logging
    logger = setup_logging(
        log_dir="artifacts/logs",
        metrics_file="artifacts/metrics.json"
    )
    
    logger.info("Logging infrastructure setup complete.")
    log_metric("setup_complete", True, metadata={"task": "T008", "timestamp": datetime.now().isoformat()})
    
    print("Logging setup complete. Logs will be written to artifacts/logs/")
    print("Metrics will be written to artifacts/metrics.json")

if __name__ == "__main__":
    main()