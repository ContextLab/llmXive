"""
Logging infrastructure for the llmXive science pipeline.

Configures a centralized logging setup that records:
- Subject exclusions (e.g., motion threshold failures)
- Processing steps and their outcomes
- Errors and warnings during data acquisition and analysis

Logs are written to:
- A rotating file: data/logs/pipeline.log
- Console (stdout) for immediate feedback
"""
import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# Import project root helper from existing config module
from config.env_manager import get_project_root


def setup_logging(
    log_level: int = logging.INFO,
    log_file_name: str = "pipeline.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    console_output: bool = True,
) -> logging.Logger:
    """
    Configure the root logger for the project.

    Args:
        log_level: The logging level (e.g., logging.INFO, logging.DEBUG).
        log_file_name: The name of the log file (stored in data/logs/).
        max_bytes: Maximum size of a log file before rotation.
        backup_count: Number of backup files to keep.
        console_output: Whether to also log to stdout.

    Returns:
        The configured root logger.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    if root_logger.handlers:
        root_logger.handlers.clear()

    project_root = get_project_root()
    log_dir = project_root / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file_path = log_dir / log_file_name

    # File Handler with rotation
    file_handler = RotatingFileHandler(
        log_file_path, maxBytes=max_bytes, backupCount=backup_count
    )
    file_handler.setLevel(log_level)

    # Formatter: [Timestamp] [Level] [Module] Message
    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)

    root_logger.addHandler(file_handler)

    # Console Handler (optional)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    return root_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a logger instance, optionally scoped to a module.

    Args:
        name: The name of the logger (e.g., "data.download_hcp").
             If None, returns the root logger.

    Returns:
        A configured Logger instance.
    """
    if name:
        return logging.getLogger(name)
    return logging.getLogger()


def log_subject_exclusion(
    subject_id: str, reason: str, logger: Optional[logging.Logger] = None
) -> None:
    """
    Log a subject exclusion event with standardized formatting.

    Args:
        subject_id: The ID of the excluded subject.
        reason: The reason for exclusion (e.g., "Mean FD >= 0.2mm").
        logger: The logger to use. If None, uses the root logger.
    """
    if logger is None:
        logger = get_logger()
    logger.warning(f"SUBJECT_EXCLUDED | ID: {subject_id} | Reason: {reason}")


def log_processing_step(
    step_name: str,
    status: str,
    details: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> None:
    """
    Log a processing step completion or failure.

    Args:
        step_name: Name of the processing step (e.g., "download_hcp").
        status: Status string (e.g., "SUCCESS", "FAILED", "SKIPPED").
        details: Optional additional details about the step.
        logger: The logger to use. If None, uses the root logger.
    """
    if logger is None:
        logger = get_logger()

    message = f"PROCESSING_STEP | {step_name} | Status: {status}"
    if details:
        message += f" | Details: {details}"

    if status == "FAILED":
        logger.error(message)
    elif status == "SUCCESS":
        logger.info(message)
    else:
        logger.warning(message)


# Example usage / CLI entry point for testing logging setup
def main() -> None:
    """
    CLI entry point to test logging configuration.
    """
    setup_logging()
    logger = get_logger("T006_Test")

    logger.info("Logging infrastructure initialized successfully.")
    log_subject_exclusion("100307", "Mean FD = 0.25mm (Threshold: 0.2mm)", logger)
    log_processing_step("data_validation", "SUCCESS", "All required columns present", logger)
    log_processing_step("motion_filter", "SUCCESS", "Excluded 12 subjects", logger)

    # Simulate an error
    try:
        raise ValueError("Simulated error for logging demonstration")
    except Exception as e:
        logger.exception(f"Processing failed with error: {e}")


if __name__ == "__main__":
    main()
