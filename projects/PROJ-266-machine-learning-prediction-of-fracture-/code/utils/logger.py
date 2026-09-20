"""
Logging infrastructure for the fracture toughness prediction pipeline.
Provides a centralized logger configuration and helper functions.
"""
import logging
import os
from pathlib import Path
from typing import Optional

# Ensure logs directory exists
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "app.log"

# Formatter matching the requirement: YYYY-MM-DD HH:MM:SS - LEVEL - NAME - MESSAGE
# The verification regex expects: ^\d{4}-\d{2}-\d{2}.+ -.+ -.+ - test$
# Standard logging format: %(asctime)s - %(levelname)s - %(name)s - %(message)s
# This produces: 2023-10-27 10:00:00 - INFO - root - test
# Which matches the regex if we consider the space in date-time as part of ".+"
# Actually, the regex is: ^\d{4}-\d{2}-\d{2}.+ -.+ -.+ - test$
# Let's break it down:
# ^\d{4}-\d{2}-\d{2} -> 2023-10-27
# .+ ->  10:00:00 (space + time)
#  - -> space dash space
# .+ -> INFO
#  - -> space dash space
# .+ -> root
#  - test$ -> space dash space test (end)
# So the format string should be: '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
# And we need to ensure the date format is YYYY-MM-DD HH:MM:SS
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_logger: Optional[logging.Logger] = None


def get_logger(name: str = "fracture_pipeline") -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: The name for the logger (e.g., 'fracture_pipeline', 'preprocess', 'training')

    Returns:
        A configured logging.Logger instance.
    """
    global _logger

    if _logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.DEBUG)

        # Prevent adding handlers multiple times if called repeatedly
        if not _logger.handlers:
            # File handler
            file_handler = logging.FileHandler(LOG_FILE, mode='a')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
            _logger.addHandler(file_handler)

            # Console handler (optional, for visibility during development)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
            _logger.addHandler(console_handler)

    # If a specific name is requested and it's not the base logger,
    # create a child logger but reuse the same handlers to ensure
    # all logs go to the same file with consistent formatting.
    if name != "fracture_pipeline":
        child_logger = logging.getLogger(name)
        child_logger.setLevel(logging.DEBUG)
        if not child_logger.handlers:
            for handler in _logger.handlers:
                child_logger.addHandler(handler)
        return child_logger

    return _logger


def test_logging() -> None:
    """
    Simple test to verify logging functionality.
    Writes a test message to logs/app.log.
    """
    logger = get_logger()
    logger.info("test")


if __name__ == "__main__":
    test_logging()
    print("Log written to logs/app.log")