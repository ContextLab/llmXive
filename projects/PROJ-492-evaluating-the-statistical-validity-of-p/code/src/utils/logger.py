"""
Structured logging infrastructure for the A/B test audit pipeline.

This module provides a centralized logging configuration that ensures all
logs follow a consistent format, including error codes in the format 'ERR-###'.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Error code registry
ERROR_CODES: Dict[int, str] = {
    # General errors
    1: "ERR-001",
    2: "ERR-002",
    # URL and fetching errors
    10: "ERR-010",
    11: "ERR-011",
    12: "ERR-012",
    # Extraction errors
    20: "ERR-020",
    21: "ERR-021",
    22: "ERR-022",
    # Statistical errors
    30: "ERR-030",
    31: "ERR-031",
    # Validation errors
    40: "ERR-040",
    41: "ERR-041",
    # Resource errors
    50: "ERR-050",
    51: "ERR-051",
    # Export errors
    60: "ERR-060",
    61: "ERR-061",
    # Monte Carlo errors
    70: "ERR-070",
    71: "ERR-071",
    # Power analysis errors
    80: "ERR-080",
    81: "ERR-081",
    # Prevalence errors
    90: "ERR-090",
    91: "ERR-091",
    # Subgroup analysis errors
    100: "ERR-100",
    101: "ERR-101",
    # Bias adjustment errors
    110: "ERR-110",
    111: "ERR-111",
    # Manifest errors
    120: "ERR-120",
    121: "ERR-121",
    # Schema validation errors
    130: "ERR-130",
    131: "ERR-131",
    # Export consistency errors
    200: "ERR-200",
    201: "ERR-201",
    # Resource limit errors
    300: "ERR-300",
    301: "ERR-301",
    # Pipeline execution errors
    800: "ERR-800",
    801: "ERR-801",
    802: "ERR-802",
}


def get_error_message(code: int) -> str:
    """
    Get the formatted error code string for a given error number.

    Args:
        code: The error number (e.g., 1 for ERR-001)

    Returns:
        Formatted error code string (e.g., 'ERR-001')
    """
    return ERROR_CODES.get(code, f"ERR-{code:03d}")


class AuditLogger:
    """
    A logger wrapper that ensures all error messages include proper error codes.
    """

    def __init__(self, name: str, log_file: Optional[Path] = None):
        """
        Initialize the audit logger.

        Args:
            name: Logger name (typically module name)
            log_file: Optional path to a log file. If None, logs to console.
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers = []  # Clear existing handlers

        # Create formatter with error code support
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def log_error(self, code: int, message: str, **kwargs: Any) -> None:
        """
        Log an error with a specific error code.

        Args:
            code: Error code number
            message: Error message
            **kwargs: Additional context to include
        """
        error_code_str = get_error_message(code)
        full_message = f"{error_code_str} - {message}"
        if kwargs:
            full_message += f" | Context: {kwargs}"
        self.logger.error(full_message)

    def log_warning(self, code: Optional[int], message: str, **kwargs: Any) -> None:
        """
        Log a warning, optionally with an error code.

        Args:
            code: Optional error code number
            message: Warning message
            **kwargs: Additional context to include
        """
        if code is not None:
            error_code_str = get_error_message(code)
            full_message = f"{error_code_str} - {message}"
        else:
            full_message = message
        if kwargs:
            full_message += f" | Context: {kwargs}"
        self.logger.warning(full_message)

    def log_info(self, message: str, **kwargs: Any) -> None:
        """
        Log an informational message.

        Args:
            message: Info message
            **kwargs: Additional context to include
        """
        full_message = message
        if kwargs:
            full_message += f" | Context: {kwargs}"
        self.logger.info(full_message)

    def log_debug(self, message: str, **kwargs: Any) -> None:
        """
        Log a debug message.

        Args:
            message: Debug message
            **kwargs: Additional context to include
        """
        full_message = message
        if kwargs:
            full_message += f" | Context: {kwargs}"
        self.logger.debug(full_message)

    def log_success(self, code: Optional[int], message: str, **kwargs: Any) -> None:
        """
        Log a success message, optionally with a completion code.

        Args:
            code: Optional success code number
            message: Success message
            **kwargs: Additional context to include
        """
        if code is not None:
            success_code_str = get_error_message(code)  # Reuse format for consistency
            full_message = f"{success_code_str} - {message}"
        else:
            full_message = f"SUCCESS - {message}"
        if kwargs:
            full_message += f" | Context: {kwargs}"
        self.logger.info(full_message)


# Global logger instance for convenience
_default_logger: Optional[AuditLogger] = None


def get_default_logger() -> AuditLogger:
    """
    Get or create the default audit logger instance.

    Returns:
        The default AuditLogger instance
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = AuditLogger("audit_pipeline")
    return _default_logger


def configure_logging(log_level: str = "INFO", log_file: Optional[Path] = None) -> None:
    """
    Configure the root logging settings for the entire application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to a log file
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logging.getLogger().addHandler(file_handler)
