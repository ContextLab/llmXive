"""
Script to initialize the logging infrastructure for the project.
Ensures the log directory exists and configures the root logger.
"""
import os
import sys
from pathlib import Path

# Add code directory to path to import lib modules
project_root = Path(__file__).resolve().parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from lib.logging_config import setup_logging, get_logger


def main():
    """Initialize logging and verify the log file is created."""
    log_path = "data/results/execution.log"
    
    # Initialize logging
    logger = setup_logging(log_file_path=log_path, level=10, console_output=True)
    
    # Log startup message
    logger.info("Logging infrastructure initialized.", extra_data={"status": "ready", "log_file": log_path})
    
    # Verify file existence
    full_path = project_root / log_path
    if full_path.exists():
        logger.info(f"Log file successfully created at: {full_path}")
    else:
        logger.error(f"Failed to create log file at: {full_path}")
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())
