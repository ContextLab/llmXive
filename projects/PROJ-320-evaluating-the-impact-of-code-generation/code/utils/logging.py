"""
Logging infrastructure for the llmXive research pipeline.

Provides a unified logging setup with file rotation for data and reports directories.
Ensures logs are persisted to disk under data/logs/ and reports/logs/.
"""
import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# Ensure project root is recognized to locate data/ and reports/ relative to it
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_LOG_DIR = PROJECT_ROOT / "data" / "logs"
REPORTS_LOG_DIR = PROJECT_ROOT / "reports" / "logs"

# Ensure log directories exist
DATA_LOG_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_LOG_DIR.mkdir(parents=True, exist_ok=True)

_logger: Optional[logging.Logger] = None

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get or create a configured logger instance.
    
    Args:
        name: Name of the logger (usually __name__ of the caller).
    
    Returns:
        A configured logging.Logger instance with file handlers.
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.DEBUG)
        
        # Avoid adding handlers multiple times if called repeatedly
        if _logger.handlers:
            return _logger

        # Formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console Handler (INFO and above)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        _logger.addHandler(console_handler)

        # Data Log Handler (RotatingFileHandler for data/ logs)
        data_log_file = DATA_LOG_DIR / "data_processing.log"
        data_handler = RotatingFileHandler(
            data_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        data_handler.setLevel(logging.DEBUG)
        data_handler.setFormatter(formatter)
        _logger.addHandler(data_handler)

        # Reports Log Handler (RotatingFileHandler for reports/ logs)
        reports_log_file = REPORTS_LOG_DIR / "report_generation.log"
        reports_handler = RotatingFileHandler(
            reports_log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        reports_handler.setLevel(logging.DEBUG)
        reports_handler.setFormatter(formatter)
        _logger.addHandler(reports_handler)

    return _logger

def setup_logging(name: str = "llmXive") -> logging.Logger:
    """
    Alias for get_logger to ensure explicit initialization if preferred.
    """
    return get_logger(name)
