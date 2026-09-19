import os
import sys
import logging
from datetime import datetime
from pathlib import Path

from config import get_path_env_override


def ensure_directories():
    """Ensure that all required logging directories exist."""
    log_dir = get_path_env_override("RESULTS_LOGS_DIR", "results/logs")
    Path(log_dir).mkdir(parents=True, exist_ok=True)


def setup_logging(
    log_file_name: str = "pipeline.log",
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Configure the root logger to write to a file and stdout.

    Args:
        log_file_name: Name of the log file (relative to results/logs/).
        level: Logging level (e.g., logging.INFO, logging.DEBUG).

    Returns:
        The configured root logger.
    """
    ensure_directories()

    log_dir = get_path_env_override("RESULTS_LOGS_DIR", "results/logs")
    log_path = Path(log_dir) / log_file_name

    # Avoid adding handlers multiple times if setup_logging is called repeatedly
    if not any(isinstance(h, logging.FileHandler) for h in logging.root.handlers):
        # Clear existing handlers to prevent duplicates
        logging.root.handlers.clear()

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # File handler
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)

        logging.root.addHandler(file_handler)
        logging.root.addHandler(console_handler)
        logging.root.setLevel(level)

    return logging.root


def get_data_quality_logger(name: str = "data_quality") -> logging.Logger:
    """
    Get a logger specifically for data quality checks and validation logs.

    Args:
        name: Name of the logger.

    Returns:
        A configured logger instance.
    """
    ensure_directories()
    logger = logging.getLogger(name)
    if not logger.handlers:
        log_dir = get_path_env_override("RESULTS_LOGS_DIR", "results/logs")
        log_path = Path(log_dir) / f"{name}.log"

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )

        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)

    return logger


def get_model_diagnostics_logger(name: str = "model_diagnostics") -> logging.Logger:
    """
    Get a logger specifically for model diagnostics and training logs.

    Args:
        name: Name of the logger.

    Returns:
        A configured logger instance.
    """
    ensure_directories()
    logger = logging.getLogger(name)
    if not logger.handlers:
        log_dir = get_path_env_override("RESULTS_LOGS_DIR", "results/logs")
        log_path = Path(log_dir) / f"{name}.log"

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )

        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)

    return logger


def main():
    """
    Entry point for testing the logging setup.
    Writes a test message to the log files.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Logging infrastructure initialized successfully.")

    data_logger = get_data_quality_logger()
    data_logger.info("Data quality logger ready.")

    model_logger = get_model_diagnostics_logger()
    model_logger.info("Model diagnostics logger ready.")


if __name__ == "__main__":
    main()
