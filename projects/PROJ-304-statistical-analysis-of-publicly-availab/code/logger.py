import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from linting_config import get_project_root

LOG_FILE_NAME = "pipeline.log"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3
FORMAT_STRING = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

_logger_instance: logging.Logger | None = None


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Returns a configured logger instance for the project.
    The logger uses a RotatingFileHandler to manage log file size.
    """
    global _logger_instance

    if _logger_instance is not None and _logger_instance.name == name:
        return _logger_instance

    root_path = get_project_root()
    log_dir = root_path / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file_path = log_dir / LOG_FILE_NAME

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers to prevent duplicates if called multiple times
    if logger.handlers:
        logger.handlers.clear()

    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(FORMAT_STRING)
    file_handler.setFormatter(formatter)

    # Also add a console handler for immediate visibility
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _logger_instance = logger
    return logger


def test_log_format() -> bool:
    """
    Unit test function to verify the log output format matches the specification.
    Returns True if the format matches, False otherwise.
    """
    logger = get_logger("test_logger_format")
    logger.handlers.clear()  # Ensure clean state for testing

    # Create an in-memory string handler to capture output
    import io
    from logging import StreamHandler

    stream = io.StringIO()
    handler = StreamHandler(stream)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(FORMAT_STRING)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Emit a test log
    test_msg = "Test log message for format verification"
    logger.info(test_msg)

    # Retrieve output
    output = stream.getvalue().strip()

    # Verify format components
    # Expected: YYYY-MM-DD HH:MM:SS,mmm - test_logger_format - INFO - Test log message for format verification
    parts = output.split(" - ")

    if len(parts) != 4:
        return False

    timestamp_part, name_part, level_part, message_part = parts

    # Check Name
    if name_part != "test_logger_format":
        return False

    # Check Level
    if level_part != "INFO":
        return False

    # Check Message
    if message_part != test_msg:
        return False

    # Check Timestamp format (basic check for presence of date/time structure)
    # Format: YYYY-MM-DD HH:MM:SS,mmm
    if len(timestamp_part) < 19:
        return False
    if "T" in timestamp_part or "Z" in timestamp_part:
        # ISO format check if standard logging deviates, though standard is usually space separated
        pass

    return True


if __name__ == "__main__":
    # Run the test if executed directly
    print("Running log format verification test...")
    if test_log_format():
        print("SUCCESS: Log format verified.")
    else:
        print("FAILURE: Log format does not match specification.")
        exit(1)
