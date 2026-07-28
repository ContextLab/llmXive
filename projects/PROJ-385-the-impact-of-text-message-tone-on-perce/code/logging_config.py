"""
Logging infrastructure configuration.
Sets up a logger that writes to data/pipeline.log.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import get_project_root, get_processed_data_dir


_logger: Optional[logging.Logger] = None


def setup_logging() -> logging.Logger:
    """
    Configures and returns the project logger.
    Writes logs to data/pipeline.log.
    """
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("llmXive_pipeline")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Create data directory if it doesn't exist
    # The log file goes in data/pipeline.log (parent of processed)
    data_dir = get_processed_data_dir().parent
    data_dir.mkdir(parents=True, exist_ok=True)

    log_file = data_dir / "pipeline.log"

    # File handler
    fh = logging.FileHandler(log_file, mode='a')
    fh.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    _logger = logger
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Gets the project logger, optionally with a specific name.
    """
    logger = setup_logging()
    if name:
        return logger.getChild(name)
    return logger


def log_pipeline_step(step_name: str, details: Optional[str] = None) -> None:
    """
    Logs a pipeline step start or completion.
    """
    logger = get_logger()
    msg = f"Pipeline Step: {step_name}"
    if details:
        msg += f" - {details}"
    logger.info(msg)


def log_exclusion(reason: str, participant_id: Optional[str] = None) -> None:
    """
    Logs a participant exclusion reason.
    """
    logger = get_logger()
    msg = f"Exclusion: {reason}"
    if participant_id:
        msg += f" (Participant: {participant_id})"
    logger.warning(msg)
