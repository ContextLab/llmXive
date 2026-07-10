import logging
import os
from pathlib import Path
from typing import Optional

# Ensure the logs directory exists
LOG_DIR = Path(__file__).parent.parent.parent / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Default log file path
DEFAULT_LOG_FILE = LOG_DIR / "pipeline.log"

# Global logger instance
_logger: Optional[logging.Logger] = None


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves or creates a logger instance configured to write to the project log file.
    
    Args:
        name: Optional name for the logger. If None, returns the root logger configured
              for this project.
    
    Returns:
        A configured logging.Logger instance.
    """
    global _logger
    
    if _logger is None:
        _logger = logging.getLogger("llmXive")
        _logger.setLevel(logging.INFO)
        
        # Avoid adding handlers multiple times if this function is called repeatedly
        if not _logger.handlers:
            # File handler
            file_handler = logging.FileHandler(str(DEFAULT_LOG_FILE))
            file_handler.setLevel(logging.INFO)
            
            # Console handler (optional, for immediate feedback)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            
            # Formatter
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            _logger.addHandler(file_handler)
            _logger.addHandler(console_handler)
    
    if name:
        return logging.getLogger(f"llmXive.{name}")
    return _logger


def log_message(message: str, level: str = "info") -> None:
    """
    Logs a message at the specified level using the project logger.
    
    Args:
        message: The message to log.
        level: The log level ('debug', 'info', 'warning', 'error', 'critical').
    """
    logger = get_logger()
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message)


def get_log_file_path() -> Path:
    """Returns the path to the current log file."""
    return DEFAULT_LOG_FILE
