import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def get_logger(name: str = "perovskite_pipeline") -> logging.Logger:
    """
    Configure and return a logger that writes to logs/pipeline.log.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "pipeline.log"

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3
    )
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def log_exclusion_reason(reason: str, record_id: str, logger: logging.Logger = None) -> None:
    """
    Log a reason why a data record was excluded from the dataset.
    """
    log = logger or get_logger()
    log.warning(f"Exclusion [ID={record_id}]: {reason}")

def log_pipeline_event(event: str, logger: logging.Logger = None) -> None:
    """
    Log a general pipeline event.
    """
    log = logger or get_logger()
    log.info(f"Pipeline Event: {event}")
