"""
Script to initialize the logging infrastructure.
This script ensures the logging directory exists and configures the logger.
It does NOT produce logs/preprocess_counts.yaml (that is handled by T013).
"""
import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from config import LOGS_DIR
from logging_config import setup_logger, get_logger

def main():
    """Initialize logging infrastructure."""
    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Logs directory ensured at: {LOGS_DIR}")

    # Setup the main logger
    logger = setup_logger("llmXive", level=20)  # INFO level
    logger.info("Logging infrastructure initialized successfully.")
    
    # Verify log file creation
    log_file = LOGS_DIR / "pipeline.log"
    if log_file.exists():
        logger.info(f"Log file created at: {log_file}")
    else:
        logger.warning("Log file was not created immediately.")
    
    print("Logging infrastructure ready. No preprocess counts generated yet (T013).")

if __name__ == "__main__":
    main()