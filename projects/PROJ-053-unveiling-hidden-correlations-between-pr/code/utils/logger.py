import logging
import time
from contextlib import contextmanager
from typing import Optional
from pathlib import Path

from config import get_logger, ensure_directories, get_logs_dir

def setup_logging(log_level: int = logging.INFO) -> str:
    """
    Setup logging infrastructure.
    
    Returns:
        Path to the log file.
    """
    ensure_directories([get_logs_dir()])
    log_file = Path(get_logs_dir()) / "pipeline.log"
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return str(log_file)

@contextmanager
def log_execution_time(task_name: str):
    """Context manager to log execution time of a block."""
    start = time.time()
    logger = logging.getLogger(__name__)
    logger.info(f"Starting task: {task_name}")
    try:
        yield
    finally:
        end = time.time()
        logger.info(f"Completed task: {task_name} in {end - start:.2f} seconds")

def log_error_and_raise(exception: Exception, message: str):
    """Log an error and re-raise the exception."""
    logger = logging.getLogger(__name__)
    logger.error(f"{message}: {exception}")
    raise exception

def get_log_file_path() -> str:
    return str(Path(get_logs_dir()) / "pipeline.log")
