import logging
import sys
from pathlib import Path
from typing import Optional

LOG_FILE_PATH = Path("data/results/pipeline_run.log")

def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """Initialize the logging infrastructure for the pipeline."""
    if log_file is None:
        log_file = LOG_FILE_PATH

    # Ensure directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("pipeline")

def get_logger(name: str = "pipeline") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
