import sys
import os
from datetime import datetime
from utils.logging_utils import setup_logging, log_metric, flush_metrics
from config import ensure_directories

def main() -> None:
    """
    Initialize the logging infrastructure and verify directory creation.
    This script ensures that artifacts/logs and artifacts/metrics.json
    are ready for use by other pipeline stages.
    """
    print("Initializing logging infrastructure...")
    
    # Ensure base directories exist
    ensure_directories()
    
    # Setup logging
    logger = setup_logging()
    
    # Verify artifacts directory exists
    artifacts_dir = "artifacts"
    logs_dir = os.path.join(artifacts_dir, "logs")
    
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        logger.warning(f"Created missing directory: {logs_dir}")
    
    # Log initialization event
    log_metric("logging_init", True, step=0)
    log_metric("init_timestamp", datetime.now().isoformat(), step=0)
    
    # Verify metrics.json creation
    metrics_path = os.path.join(artifacts_dir, "metrics.json")
    if os.path.exists(metrics_path):
        logger.info(f"Metrics file ready at: {metrics_path}")
    else:
        logger.error("Failed to create metrics file.")
        sys.exit(1)
        
    logger.info("Logging infrastructure setup complete.")
    flush_metrics()

if __name__ == "__main__":
    main()