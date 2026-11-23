import logging
import sys
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# Ensure the logs directory exists relative to project root
# Assuming the script is run from the project root or code/
LOG_DIR = Path.cwd() / "logs"
if not LOG_DIR.exists():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "pipeline.log"

class StructuredFormatter(logging.Formatter):
    """
    A custom formatter that outputs log records in a structured format.
    Format: [LEVEL] [TIMESTAMP] [MODULE] [MESSAGE]
    """

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, self.datefmt)
        # Extract module name from the full logger name
        module_name = record.name.split('.')[-1] if '.' in record.name else record.name
        return (
            f"[{record.levelname}] "
            f"[{timestamp}] "
            f"[{module_name}] "
            f"{record.getMessage()}"
        )

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Retrieves or creates a logger with the specified name.
    Configures handlers for stdout and rotating file output.

    Args:
        name: The name of the logger (typically __name__).
        level: The logging level (default: INFO).

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Formatter
    formatter = StructuredFormatter()

    # Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # File Handler (RotatingFileHandler to manage disk usage)
    # Max size 10MB, keep 5 backup files
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

def main():
    """
    Demonstration of the logger usage.
    """
    logger = get_logger("T006_Demo")

    logger.info("Logger initialized successfully.")
    logger.debug("This is a debug message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")

    # Verify log file creation
    if LOG_FILE.exists():
        logger.info(f"Log file created at: {LOG_FILE.absolute()}")
    else:
        logger.error("Log file was not created.")

if __name__ == "__main__":
    main()