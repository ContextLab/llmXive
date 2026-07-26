"""
Script to setup logging infrastructure.
"""
import sys
import os
from datetime import datetime
from utils.logging_utils import setup_logging, log_metric, flush_metrics
from config import ensure_directories

def main():
    """Setup logging and create initial log files."""
    from config import get_config
    cfg = get_config()
    
    # Ensure log directories exist
    ensure_directories([cfg['artifacts_dir']])
    
    # Setup logging
    logger = setup_logging()
    logger.info("Logging infrastructure initialized.")
    
    # Log a test metric
    log_metric("setup", "timestamp", datetime.now().isoformat())
    flush_metrics()
    print("Logging setup complete.")

if __name__ == "__main__":
    main()
