import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from tqdm import tqdm

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Configures and returns a logger.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    
    # Create console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    ch.setFormatter(formatter)
    
    logger.addHandler(ch)
    return logger

def setup_progress_bar(total: int, desc: str = "Progress") -> tqdm:
    """
    Creates and returns a tqdm progress bar.
    """
    return tqdm(total=total, desc=desc, unit="item")

def log_metric(name: str, data: Dict[str, Any]):
    """
    Logs a metric to the logger.
    """
    logger = get_logger(__name__)
    logger.info(f"METRIC[{name}]: {data}")

def log_error_summary(error: Exception, context: Optional[str] = None):
    """
    Logs an error summary.
    """
    logger = get_logger(__name__)
    msg = f"ERROR: {error}"
    if context:
        msg += f" (Context: {context})"
    logger.error(msg)

def main():
    """
    Main entry point for testing the logger module.
    """
    logger = get_logger("test_logger")
    logger.info("Logger initialized successfully.")
    log_metric("test_metric", {"key": "value"})
    log_error_summary(ValueError("Test error"), "Testing error logging")

if __name__ == "__main__":
    main()
