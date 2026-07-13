import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from seeds import get_seed_value
from checksum import compute_sha256


# Constants
LOG_DIR = Path("logs")
LOG_FILE_NAME = "pipeline.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = logging.INFO


_loggers: Dict[str, logging.Logger] = {}


def _ensure_log_dir() -> Path:
    """Ensure the log directory exists."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR


def _get_file_handler(log_path: Path) -> logging.FileHandler:
    """Create a file handler with the standard format."""
    handler = logging.FileHandler(log_path)
    handler.setLevel(LOG_LEVEL)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    handler.setFormatter(formatter)
    return handler


def _get_console_handler() -> logging.StreamHandler:
    """Create a console handler with the standard format."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(LOG_LEVEL)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    handler.setFormatter(formatter)
    return handler


def setup_logger(
    name: str,
    snippet_id: Optional[str] = None,
    log_level: int = LOG_LEVEL,
    file_path: Optional[Path] = None,
) -> logging.Logger:
    """
    Setup and return a logger instance.

    The logger is snippet-ID aware if a snippet_id is provided.
    It logs to both console and a file (defaulting to logs/pipeline.log).

    Args:
        name: The name of the logger (usually module name).
        snippet_id: Optional snippet ID to include in the logger's name.
        log_level: Logging level (default: INFO).
        file_path: Optional custom path for the log file.

    Returns:
        A configured logging.Logger instance.
    """
    if snippet_id:
        full_name = f"{name}[snippet:{snippet_id}]"
    else:
        full_name = name

    # Return existing logger if already configured
    if full_name in _loggers:
        logger = _loggers[full_name]
        logger.setLevel(log_level)
        return logger

    logger = logging.getLogger(full_name)
    logger.setLevel(log_level)

    # Avoid adding handlers multiple times if the logger is reused
    if logger.handlers:
        logger.handlers.clear()

    # Add console handler
    console_handler = _get_console_handler()
    logger.addHandler(console_handler)

    # Add file handler
    if file_path is None:
        log_dir = _ensure_log_dir()
        file_path = log_dir / LOG_FILE_NAME
    else:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = _get_file_handler(file_path)
    logger.addHandler(file_handler)

    # Prevent propagation to root logger to avoid duplicate console logs
    logger.propagate = False

    _loggers[full_name] = logger
    return logger


def get_logger(name: str, snippet_id: Optional[str] = None) -> logging.Logger:
    """
    Retrieve an existing logger or create a new one if it doesn't exist.
    This is a convenience wrapper around setup_logger.

    Args:
        name: The name of the logger.
        snippet_id: Optional snippet ID to include in the logger's name.

    Returns:
        A configured logging.Logger instance.
    """
    return setup_logger(name, snippet_id=snippet_id)


def log_snippet_info(
    logger: logging.Logger,
    snippet_id: str,
    source: str,
    language: str,
    length: int,
) -> None:
    """
    Log standardized information about a code snippet.

    Args:
        logger: The logger instance to use.
        snippet_id: The unique identifier for the snippet.
        source: The source of the snippet (e.g., 'CodeSearchNet', 'CodeGen').
        language: The programming language.
        length: The length of the code (e.g., number of lines or characters).
    """
    logger.info(
        f"Processing snippet: id={snippet_id}, source={source}, "
        f"language={language}, length={length}"
    )


def log_metric_extraction(
    logger: logging.Logger,
    snippet_id: str,
    metric_type: str,
    score: float,
    timestamp: Optional[datetime] = None,
) -> None:
    """
    Log the extraction of a metric score for a snippet.

    Args:
        logger: The logger instance to use.
        snippet_id: The unique identifier for the snippet.
        metric_type: The type of metric (e.g., 'cyclomatic_complexity').
        score: The calculated score.
        timestamp: Optional timestamp for the metric.
    """
    ts = timestamp or datetime.now()
    logger.info(
        f"Metric extracted: snippet_id={snippet_id}, type={metric_type}, "
        f"score={score:.4f}, timestamp={ts.isoformat()}"
    )


def log_error(
    logger: logging.Logger,
    snippet_id: Optional[str],
    error_code: int,
    message: str,
) -> None:
    """
    Log a structured error message.

    Args:
        logger: The logger instance to use.
        snippet_id: Optional snippet ID related to the error.
        error_code: Numeric error code.
        message: Human-readable error message.
    """
    snippet_info = f" [snippet_id={snippet_id}]" if snippet_id else ""
    logger.error(
        f"Error {error_code}{snippet_info}: {message}",
        exc_info=True,
    )


def main() -> None:
    """
    Demonstrate the logging configuration.
    """
    logger = get_logger("logging_config_demo")
    logger.info("Logging infrastructure initialized.")
    logger.info(f"Seed value from seeds module: {get_seed_value()}")

    # Simulate snippet processing
    snippet_id = "demo-001"
    logger = get_logger("data_ingestion", snippet_id=snippet_id)
    log_snippet_info(
        logger,
        snippet_id=snippet_id,
        source="CodeSearchNet",
        language="python",
        length=150,
    )

    # Simulate metric extraction
    log_metric_extraction(
        logger,
        snippet_id=snippet_id,
        metric_type="cyclomatic_complexity",
        score=4.5,
    )

    # Simulate error
    log_error(
        logger,
        snippet_id=snippet_id,
        error_code=101,
        message="Dataset verification failed.",
    )

    logger.info("Demo completed successfully.")


if __name__ == "__main__":
    main()