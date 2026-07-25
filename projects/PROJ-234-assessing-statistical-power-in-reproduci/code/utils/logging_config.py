"""
Logging configuration for the pipeline.
"""
import logging
import os
from pathlib import Path

def setup_logging(log_file: str = "data/ingest.log") -> logging.Logger:
    """
    Configure logging to write to a file and console.
    
    Args:
        log_file: Path to the log file.
        
    Returns:
        The root logger.
    """
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
        filemode='a'
    )

    # Also log to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    console.setFormatter(console_formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(console)
    
    return root_logger

def test_log_entry() -> None:
    """
    Write a test entry to the log file to verify configuration.
    """
    logger = logging.getLogger(__name__)
    logger.info("Test log entry: Logging configuration is active.")
    logger.info(f"Log file path: {Path('data/ingest.log').absolute()}")
