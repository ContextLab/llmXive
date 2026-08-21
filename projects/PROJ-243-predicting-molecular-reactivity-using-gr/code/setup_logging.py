import sys
import os
from datetime import datetime
from utils.logging_utils import setup_logging, log_metric, flush_metrics
from config import ensure_directories, get_config

def setup_script_logging(script_name: str) -> None:
    """
    Initialize logging for a specific script.
    
    This function creates a timestamped log file in artifacts/logs/
    and configures the global logger.
    
    Args:
        script_name: The name of the script (e.g., '01_download_data').
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{script_name}_{timestamp}.log"
    log_path = os.path.join("artifacts", "logs", log_filename)
    
    # Ensure directory exists
    ensure_directories([os.path.dirname(log_path)])
    
    # Initialize logger
    setup_logging(log_file=log_path, log_level=logging.INFO)
    
    # Log initial script info
    logger = get_logger()
    logger.info(f"Script '{script_name}' started at {datetime.now().isoformat()}")

def main():
    """
    Standalone runner to verify logging infrastructure setup.
    This script ensures the directory structure exists and writes a test log.
    """
    # Simulate a script run
    script_name = "setup_logging"
    setup_script_logging(script_name)
    
    logger = get_logger()
    logger.info("Infrastructure verification successful.")
    
    # Write a dummy metric to verify metrics.json creation
    log_metric("setup_status", "success")
    flush_metrics("artifacts/metrics.json")
    
    logger.info("Metrics flushed to artifacts/metrics.json")
    print(f"Logging setup complete. Log file: artifacts/logs/{script_name}_*.log")
    print("Metrics file: artifacts/metrics.json")

if __name__ == "__main__":
    main()