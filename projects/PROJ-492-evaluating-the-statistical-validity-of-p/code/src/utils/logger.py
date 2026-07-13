"""
Structured logging infrastructure for the A/B Test Audit Pipeline.

This module provides a centralized logging configuration that ensures all log
messages follow a consistent format, including error codes in the format ERR-###.
"""

import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# Error code registry
ERROR_CODES: Dict[str, str] = {
    "ERR-001": "Missing required metric in A/B test summary",
    "ERR-002": "Inequality p-value detected (p > 1.0 or p < 0.0)",
    "ERR-003": "Malformed HTML structure preventing extraction",
    "ERR-004": "Conflicting sample sizes between variants",
    "ERR-005": "Missing baseline conversion rate",
    "ERR-006": "Sample size mismatch between reported and calculated values",
    "ERR-007": "Statistical reconstruction failed for unknown test type",
    "ERR-008": "Power analysis corpus size below minimum threshold",
    "ERR-009": "RAM limit exceeded during processing",
    "ERR-010": "Timeout exceeded during HTTP fetch",
    "ERR-050": "Schema validation failed for audit record",
    "ERR-051": "Schema validation failed for manifest",
    "ERR-100": "URL ingestion failed - CSV not found",
    "ERR-101": "URL deduplication failed - invalid data format",
    "ERR-200": "Export consistency check failed - JSON/CSV mismatch",
    "ERR-201": "Export validation: audit_report.json and summary_report.csv counts do not match",
    "ERR-300": "Resource monitoring limit breach",
    "ERR-301": "Resource limit exceeded: CPU or memory threshold breached",
    "ERR-800": "Synthetic validation thresholds not met (precision < 90% or recall < 80%)",
    "ERR-801": "Real-world validation thresholds not met",
    "ERR-802": "Extraction accuracy on real-world data failed",
    "ERR-900": "Constitution principle violation detected",
    "ERR-950": "Constitution compliance check failed",
}


class AuditLogger(logging.LoggerAdapter):
    """
    Custom logger adapter that ensures all log messages include structured
    error codes when applicable and follows the project's logging format.
    """

    def __init__(self, logger: logging.Logger, extra: Optional[Dict[str, Any]] = None):
        super().__init__(logger, extra or {})

    def get_error_code(self, msg: str, *args, **kwargs) -> Optional[str]:
        """
        Extract or generate an error code from the message or kwargs.
        Looks for 'error_code' in kwargs or extracts ERR-### from the message.
        """
        error_code = kwargs.get('error_code')
        if error_code:
            return error_code

        # Check if message contains an error code pattern
        import re
        match = re.search(r'(ERR-\d{3})', msg)
        if match:
            return match.group(1)

        return None

    def get_error_message(self, error_code: str) -> str:
        """
        Retrieve the human-readable description for an error code.
        """
        return ERROR_CODES.get(error_code, f"Unknown error: {error_code}")

    def log_with_code(self, level: int, msg: str, error_code: Optional[str] = None, *args, **kwargs):
        """
        Log a message with an explicit error code.
        """
        if error_code:
            error_desc = self.get_error_message(error_code)
            structured_msg = f"[{error_code}] {error_desc}: {msg}"
            # Add error code to extra context for JSON formatting
            extra = kwargs.get('extra', {})
            extra['error_code'] = error_code
            extra['error_description'] = error_desc
            kwargs['extra'] = extra
            self.log(level, structured_msg, *args, **kwargs)
        else:
            self.log(level, msg, *args, **kwargs)

    def error(self, msg: str, *args, error_code: Optional[str] = None, **kwargs):
        """Log an error message with optional error code."""
        self.log_with_code(logging.ERROR, msg, error_code=error_code, *args, **kwargs)

    def critical(self, msg: str, *args, error_code: Optional[str] = None, **kwargs):
        """Log a critical message with optional error code."""
        self.log_with_code(logging.CRITICAL, msg, error_code=error_code, *args, **kwargs)


class JsonFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON with structured fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add error code if present
        if hasattr(record, 'error_code'):
            log_data["error_code"] = record.error_code
            log_data["error_description"] = getattr(record, 'error_description', '')

        # Add extra fields if present
        if hasattr(record, 'extra') and record.extra:
            log_data.update({k: v for k, v in record.extra.items() if k not in log_data})

        return json.dumps(log_data)


def get_default_logger(name: str = "ab_audit") -> AuditLogger:
    """
    Create and configure a default logger for the pipeline.

    Args:
        name: The name for the logger instance.

    Returns:
        Configured AuditLogger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers if called multiple times
    if not logger.handlers:
        # Console handler with JSON formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(JsonFormatter())
        logger.addHandler(console_handler)

        # File handler for detailed logs
        log_dir = Path("data/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(log_dir / f"audit_{timestamp}.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)

    return AuditLogger(logger)


def get_error_message(error_code: str) -> str:
    """
    Retrieve the human-readable description for an error code.

    Args:
        error_code: The error code string (e.g., 'ERR-001').

    Returns:
        The error message description.
    """
    return ERROR_CODES.get(error_code, f"Unknown error code: {error_code}")


# Convenience function to create a logger for a specific module
def get_module_logger(module_name: str) -> AuditLogger:
    """
    Create a logger for a specific module with the full package path.

    Args:
        module_name: The module name (e.g., 'extractor', 'reconstructor').

    Returns:
        Configured AuditLogger instance.
    """
    return get_default_logger(f"ab_audit.{module_name}")
