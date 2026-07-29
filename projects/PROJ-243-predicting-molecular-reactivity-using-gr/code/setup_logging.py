import sys
import os
from datetime import datetime
from utils.logging_utils import setup_logging, log_metric, flush_metrics
from config import ensure_directories

def main():
    """
    Entry point for initializing the logging infrastructure.
    This script is typically called at the start of other pipeline scripts
    to ensure logs and metrics are written to the correct locations.
    """
    # Ensure all required directories exist
    ensure_directories()
    
    # Initialize logging
    # This creates artifacts/logs/pipeline.log and artifacts/logs/metrics.json
    logger = setup_logging(
        log_dir="artifacts/logs",
        log_file_name="pipeline.log",
        metrics_file_name="metrics.json",
        level=logging.INFO
    )
    
    logger.info("Logging setup completed successfully.")
    
    # Log the initialization event itself as a metric
    log_metric(
        "logging_initialized",
        True,
        stage="setup",
        details={"timestamp": datetime.utcnow().isoformat()}
    )
    
    # Explicitly flush to ensure the file exists even if script exits immediately
    flush_metrics()
    
    print("Logging infrastructure ready. Check artifacts/logs/ for output.")

if __name__ == "__main__":
    main()
