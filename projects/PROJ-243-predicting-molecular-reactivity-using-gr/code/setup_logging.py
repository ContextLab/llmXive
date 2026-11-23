import sys
import os
from datetime import datetime
from utils.logging_utils import setup_logging, log_metric, flush_metrics, log_execution_summary
from config import ensure_directories, get_config

def setup_script_logging(script_name: str) -> None:
    """
    Initialize the logging infrastructure for a specific script.
    Creates necessary directories and configures the logger.
    """
    config = get_config()
    ensure_directories(config)
    
    # Generate unique log filename based on timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{script_name}_{timestamp}.log"
    log_dir = os.path.join(config['paths']['artifacts'], 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_filename)
    
    # Initialize logging
    setup_logging(log_path)

def main():
    """
    Entry point for the logging setup script.
    Verifies that logs and metrics are written correctly.
    """
    script_name = "setup_logging"
    setup_script_logging(script_name)
    
    from utils.logging_utils import get_logger
    logger = get_logger()
    
    logger.info(f"Script {script_name} started.")
    log_metric("setup_status", "success", tags={"script": script_name})
    log_execution_summary({
        "script": script_name,
        "status": "completed",
        "message": "Logging infrastructure initialized and verified."
    })
    
    logger.info(f"Script {script_name} finished.")
    print(f"Logging setup complete. Check artifacts/logs/ and artifacts/metrics.json")

if __name__ == "__main__":
    main()