"""
Structured logging infrastructure for the A/B Test Audit Pipeline.

This module provides a centralized logging configuration that ensures all log
messages follow a consistent format, including standardized error codes (ERR-###)
as required by FR-007 and Constitution Principle VII (Provenance).
"""
import logging
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# Error code registry to ensure uniqueness and documentation
ERROR_CODES: Dict[str, str] = {
    "ERR-001": "Missing required field in extracted summary",
    "ERR-002": "Malformed HTML structure prevented extraction",
    "ERR-003": "Sample size mismatch between reported and calculated values",
    "ERR-004": "P-value inconsistency detected (absolute difference > 0.05)",
    "ERR-005": "Effect size inconsistency detected (relative difference > 5%)",
    "ERR-006": "Inequality p-value format detected (e.g., p < 0.001)",
    "ERR-007": "Conflicting sample sizes reported in source",
    "ERR-008": "Baseline conversion rate missing for binary outcome",
    "ERR-009": "Statistical test type could not be determined",
    "ERR-010": "Power analysis requirements not met (N < 300)",
    "ERR-101": "URL fetch failed after retries",
    "ERR-102": "Domain extraction failed for URL",
    "ERR-201": "Export consistency check failed (JSON vs CSV count mismatch)",
    "ERR-301": "Resource limit exceeded (CPU > 2vCPU or RAM > 2GB)",
    "ERR-800": "Evaluation threshold not met (Precision < 90% or Recall < 80%)",
    "ERR-801": "Monte-Carlo validation failed (difference > 0.005)",
    "ERR-802": "Real-world validation threshold not met",
    "ERR-950": "Constitution compliance check failed",
}

def get_error_message(code: str) -> str:
    """
    Retrieve the human-readable description for an error code.

    Args:
        code: The error code string (e.g., 'ERR-001').

    Returns:
        The error description if found, otherwise a generic message.
    """
    return ERROR_CODES.get(code, f"Unknown error code: {code}")

class AuditLogger(logging.LoggerAdapter):
    """
    A LoggerAdapter that injects structured metadata into every log record.

    This ensures that all logs produced by the audit pipeline contain:
    - Timestamp
    - Error Code (if applicable)
    - Component/Module name
    - Task ID context (if available)
    """

    def __init__(
        self,
        logger: logging.Logger,
        extra: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        task_id: Optional[str] = None,
    ):
        """
        Initialize the AuditLogger.

        Args:
            logger: The underlying logging.Logger instance.
            extra: Additional context data to inject.
            error_code: Standardized error code (ERR-###) if this log represents an error.
            task_id: The current task ID context (e.g., 'T009').
        """
        context = {
            "component": extra.get("component", "unknown") if extra else "unknown",
            "task_id": task_id or "UNKNOWN",
            "timestamp": datetime.utcnow().isoformat(),
        }
        if error_code:
            context["error_code"] = error_code
            context["error_message"] = get_error_message(error_code)
        else:
            context["error_code"] = None
            context["error_message"] = None

        super().__init__(logger, context)

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        Inject structured context into the log message.

        Args:
            msg: The original log message.
            kwargs: Keyword arguments passed to the logger.

        Returns:
            A tuple of (formatted_message, kwargs).
        """
        extra = self.extra.copy()
        # Format: [TIMESTAMP] [LEVEL] [TASK_ID] [COMPONENT] [ERR-CODE] MSG
        level = kwargs.get("level", logging.INFO)
        level_name = logging.getLevelName(level) if isinstance(level, int) else str(level)

        error_code_str = f" [{extra['error_code']}]" if extra.get('error_code') else ""

        formatted_msg = (
            f"[{extra['timestamp']}] "
            f"[{level_name}] "
            f"[{extra['task_id']}] "
            f"[{extra['component']}] "
            f"{error_code_str} "
            f"{msg}"
        )

        return formatted_msg, kwargs

def get_default_logger(
    name: Optional[str] = None,
    task_id: Optional[str] = None,
    log_file: Optional[str] = None,
) -> AuditLogger:
    """
    Create and configure a default AuditLogger instance.

    Args:
        name: Name for the logger. Defaults to the module name if None.
        task_id: The current task ID to include in all logs.
        log_file: Optional path to a file for log output. If None, logs to stderr.

    Returns:
        An configured AuditLogger instance.
    """
    if name is None:
        # Derive name from caller or default
        name = "audit_pipeline"

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers if called multiple times
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        if log_file:
            # Ensure directory exists
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(log_file)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        # Always log to stderr for visibility in CI/CLI
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return AuditLogger(logger, task_id=task_id)

def log_error(logger: AuditLogger, error_code: str, message: str, **kwargs):
    """
    Log an error message with a standardized error code.

    This is a convenience wrapper that ensures the error code is attached
    to the log record and the message is formatted correctly.

    Args:
        logger: The AuditLogger instance.
        error_code: The standardized error code (ERR-###).
        message: The human-readable error message.
        **kwargs: Additional context to merge into the log record.
    """
    if error_code not in ERROR_CODES:
        # Log a warning if the error code is unknown
        logger.warning(f"Unknown error code used: {error_code}")

    # Merge kwargs into extra context
    extra = {"component": kwargs.get("component", "unknown")}
    extra.update({k: v for k, v in kwargs.items() if k != "component"})

    # Create a temporary logger with the specific error code
    error_logger = AuditLogger(logger.logger, extra=extra, error_code=error_code)
    error_logger.error(message)

def log_warning(logger: AuditLogger, message: str, **kwargs):
    """Log a warning message."""
    extra = {"component": kwargs.get("component", "unknown")}
    extra.update({k: v for k, v in kwargs.items() if k != "component"})
    warning_logger = AuditLogger(logger.logger, extra=extra)
    warning_logger.warning(message)

def log_info(logger: AuditLogger, message: str, **kwargs):
    """Log an info message."""
    extra = {"component": kwargs.get("component", "unknown")}
    extra.update({k: v for k, v in kwargs.items() if k != "component"})
    info_logger = AuditLogger(logger.logger, extra=extra)
    info_logger.info(message)

def log_debug(logger: AuditLogger, message: str, **kwargs):
    """Log a debug message."""
    extra = {"component": kwargs.get("component", "unknown")}
    extra.update({k: v for k, v in kwargs.items() if k != "component"})
    debug_logger = AuditLogger(logger.logger, extra=extra)
    debug_logger.debug(message)
