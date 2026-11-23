import logging
import sys
from pathlib import Path
from typing import Optional

_logger_instance = None

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up logging to both console and a file if specified.
    Returns the root logger.
    """
    global _logger_instance

    if _logger_instance is not None:
        return _logger_instance

    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    _logger_instance = logger
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance. If setup_logging hasn't been called, it will set it up.
    """
    if _logger_instance is None:
        # Default log file path relative to project root
        project_root = Path(__file__).parent.parent.parent
        log_file = project_root / "data" / "results" / "pipeline_run.log"
        setup_logging(str(log_file))

    if name:
        return logging.getLogger(name)
    return _logger_instance
