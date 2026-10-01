import logging
import os
from pathlib import Path

_logger_instance = None

def get_logger(name: str = "pipeline") -> logging.Logger:
    """
    Returns a configured logger instance.
    Configures file and stdout handlers.
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = logging.getLogger(name)
        if _logger_instance.handlers:
            return _logger_instance

        # Setup directories
        log_dir = Path("data/processed")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "pipeline.log"

        # Configure format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)              # Use INFO to see verification output
        console_handler.setFormatter(formatter)

        _logger_instance = logging.getLogger(name)
        _logger_instance.setLevel(logging.INFO)
        _logger_instance.addHandler(file_handler)
        _logger_instance.addHandler(console_handler)

    return _logger_instance
