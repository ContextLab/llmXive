"""
Structured JSON logging and result artifact generation for llmXive pipeline.

Provides:
- StructuredJsonFormatter: Formats log records as JSON.
- setup_logging: Configures the root logger with file and console handlers.
- log_result_artifact: Records metadata about generated artifacts in a structured log.
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure the utils directory is treated as a package if run directly, 
# though typically imported from project root.
LOG_DIR = Path("data/logs")
RESULTS_DIR = Path("results")


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as JSON with additional context fields."""

    def __init__(self, task_id: str = "UNKNOWN"):
        super().__init__()
        self.task_id = task_id

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "task_id": self.task_id,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


def setup_logging(
    task_id: str = "T004",
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Configures the root logger with JSON formatting.
    
    Args:
        task_id: The current task identifier for tagging logs.
        log_level: The logging level (e.g., logging.INFO).
        log_file: Optional path to a log file. If None, logs to console only.
    
    Returns:
        The configured root logger.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create formatter
    formatter = StructuredJsonFormatter(task_id=task_id)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    if log_file:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_result_artifact(
    logger: logging.Logger,
    artifact_path: str,
    artifact_type: str,
    checksum: Optional[str] = None,
    size_bytes: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Logs a structured result about a generated artifact.
    
    Args:
        logger: The logger instance to use.
        artifact_path: Relative path to the artifact.
        artifact_type: Type of artifact (e.g., 'csv', 'model', 'figure').
        checksum: Optional checksum (e.g., MD5/SHA256) of the file.
        size_bytes: Optional file size in bytes.
        metadata: Optional dictionary of additional metadata.
    """
    extra = {
        "event": "artifact_generated",
        "artifact": {
            "path": artifact_path,
            "type": artifact_type,
            "checksum": checksum,
            "size_bytes": size_bytes,
        },
    }
    if metadata:
        extra["artifact"]["metadata"] = metadata

    # Attach extra data to the log record via a custom adapter or direct call
    # Since standard logging doesn't support 'extra_data' directly on call without a custom handler,
    # we will use the 'extra' mechanism and modify the formatter to look for it,
    # OR simply log a message with the data serialized if the formatter doesn't pick up 'extra'.
    # To keep it compatible with the StructuredJsonFormatter above, we'll pass it via a custom LogRecord.
    
    # Simpler approach for this specific formatter which looks for 'extra_data' attribute:
    # We can't easily set attributes on a standard LogRecord via the 'extra' dict in a simple call 
    # without a custom adapter. 
    # Let's use a simpler method: log a message that the formatter can parse, 
    # or update the formatter to handle 'extra'.
    
    # Re-implementation of the call to ensure 'extra_data' is picked up by our specific formatter:
    # The formatter checks `if hasattr(record, "extra_data")`. 
    # Standard logging 'extra' dict merges into the record.
    # So we can pass the dict in 'extra' and update the formatter to read from it.
    # However, to strictly follow the formatter logic above:
    
    # Let's update the formatter logic in the class definition to check `record.__dict__` 
    # for keys in the `extra` dict passed to `logger.info(msg, extra={...})`.
    # Actually, the standard way is:
    # record.__dict__.update(extra)
    # So if we pass `extra={"extra_data": {...}}`, it becomes `record.extra_data`.
    
    logger.info(
        f"Artifact generated: {artifact_path}",
        extra={"extra_data": extra},
    )

def log_error_summary(
    logger: logging.Logger,
    error_type: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Logs a structured error summary for failure analysis.
    """
    extra = {
        "event": "error_summary",
        "error_type": error_type,
        "message": message,
    }
    if details:
        extra["details"] = details
    
    logger.error(
        f"Error: {message}",
        extra={"extra_data": extra},
        exc_info=False, # Prevent double logging if called inside except block
    )

# If run as a script, perform a self-test
if __name__ == "__main__":
    logger = setup_logging(task_id="T004-TEST", log_file="data/logs/test_run.log")
    logger.info("Logging module initialized successfully.")
    
    # Test artifact logging
    log_result_artifact(
        logger,
        "data/processed/test.csv",
        "csv",
        checksum="abc123",
        size_bytes=1024,
        metadata={"rows": 500, "columns": 12}
    )
    
    # Test error logging
    log_error_summary(
        logger,
        "ValueError",
        "Invalid input detected during preprocessing",
        details={"row_id": 42, "column": "smiles"}
    )
    
    logger.info("Self-test completed.")
