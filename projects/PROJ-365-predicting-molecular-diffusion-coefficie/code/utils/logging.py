import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from utils.config import get_project_root, get_log_path

# Define the specific tags required by the specification
MISSING_DATA_TAG = "[MISSING_DATA_EXCLUDED]"
ERROR_SMILES_TAG = "[ERROR_SMILES]"

_logger: Optional[logging.Logger] = None
_log_file_path: Optional[Path] = None

def _init_logger() -> logging.Logger:
    """Initializes the logger if not already initialized."""
    global _logger, _log_file_path
    if _logger is not None:
        return _logger

    project_root = get_project_root()
    log_dir = project_root / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "ingestion.log"
    _log_file_path = log_file

    # Configure the root logger for this module to write to the specific file
    # We use a custom handler to ensure plain text format with timestamps
    logger = logging.getLogger("llmXive.ingestion")
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates in test environments
    logger.handlers.clear()

    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # Format: YYYY-MM-DD HH:MM:SS [TAG] Message
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    # We will inject tags manually in specific functions to match the exact string requirement
    # So the standard formatter is used, but we prepend tags in the specific calls.
    # Actually, the requirement is specific tags in the text.
    # Let's make the formatter output: timestamp message.
    # And the specific functions will format the message to include the tag.
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _logger = logger
    return logger

def get_logger() -> logging.Logger:
    """Returns the initialized logger."""
    return _init_logger()

def get_log_file_path() -> Path:
    """Returns the path to the ingestion log file."""
    _init_logger()
    return _log_file_path  # type: ignore

def log_missing_data_excluded(record_id: str, reason: str = "Missing required data") -> None:
    """
    Logs an entry with the tag [MISSING_DATA_EXCLUDED].
    Ensures the exact tag string appears in data/logs/ingestion.log.
    """
    logger = get_logger()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    message = f"{MISSING_DATA_TAG} RecordID={record_id} Reason={reason}"
    logger.info(message)

def log_invalid_smiles(record_id: str, smiles: str, error: str) -> None:
    """
    Logs an entry with the tag [ERROR_SMILES].
    Ensures the exact tag string appears in data/logs/ingestion.log.
    """
    logger = get_logger()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Truncate SMILES if too long for readability, but keep it in log
    safe_smiles = smiles[:50] + "..." if len(smiles) > 50 else smiles
    message = f"{ERROR_SMILES_TAG} RecordID={record_id} SMILES={safe_smiles} Error={error}"
    logger.info(message)

def log_info(message: str) -> None:
    """Logs a generic info message."""
    logger = get_logger()
    logger.info(message)

def log_error(message: str) -> None:
    """Logs a generic error message."""
    logger = get_logger()
    logger.error(message)
