"""
Logging configuration for the llmXive science pipeline.
Provides structured logging setup and checksum generation utilities.
"""
import logging
import json
import hashlib
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Union
from datetime import datetime

# Define a custom JSON formatter for structured logging
class JsonFormatter(logging.Formatter):
    """Formats log records as JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Union[str, Path]] = None,
    use_json: bool = False,
) -> logging.Logger:
    """
    Configure the root logger with console and optional file handlers.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If None, only console output.
        use_json: If True, use JSON structured logging format.

    Returns:
        Configured root logger.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    if use_json:
        console_handler.setFormatter(JsonFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )

    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(getattr(logging, log_level.upper()))

        if use_json:
            file_handler.setFormatter(JsonFormatter())
        else:
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )

        root_logger.addHandler(file_handler)

    return root_logger

def calculate_checksum(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Calculate the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (sha256, md5, sha1).

    Returns:
        Hexadecimal checksum string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_obj = hashlib.new(algorithm)

    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except PermissionError as e:
        raise PermissionError(f"Permission denied reading file: {file_path}") from e
    except Exception as e:
        raise RuntimeError(f"Error calculating checksum for {file_path}: {e}") from e

def log_checksum(
    logger: logging.Logger,
    file_path: Union[str, Path],
    checksum: Optional[str] = None,
    algorithm: str = "sha256",
) -> str:
    """
    Calculate and log the checksum of a file.

    Args:
        logger: Logger instance to use.
        file_path: Path to the file.
        checksum: Optional pre-calculated checksum.
        algorithm: Hash algorithm to use.

    Returns:
        The calculated checksum.
    """
    file_path = Path(file_path)
    if checksum is None:
        checksum = calculate_checksum(file_path, algorithm)

    logger.info(
        f"File checksum calculated",
        extra={"extra_data": {"file": str(file_path), "checksum": checksum, "algorithm": algorithm}},
    )

    return checksum

def create_logger(name: str) -> logging.Logger:
    """
    Create and return a logger with the given name.
    The logger will inherit configuration from the root logger.

    Args:
        name: Name for the logger.

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)

def main():
    """
    Demonstrate logging configuration and checksum functionality.
    """
    # Setup logging
    logger = setup_logging(log_level="DEBUG", use_json=True)

    logger.info("Logging configuration test started")

    # Test checksum calculation on a known file
    try:
        # Use the periodic table data file created in T006/T007
        test_file = Path("data/raw/elemental_properties.csv")
        if test_file.exists():
            checksum = log_checksum(logger, test_file)
            logger.info(f"Checksum for {test_file}: {checksum}")
        else:
            logger.warning(f"Test file not found: {test_file}")

        # Test with a non-existent file
        try:
            calculate_checksum("non_existent_file.txt")
        except FileNotFoundError as e:
            logger.error(f"Expected error: {e}")

    except Exception as e:
        logger.error(f"Error during test: {e}", exc_info=True)

    logger.info("Logging configuration test completed")

if __name__ == "__main__":
    main()