"""
Structured logging module for the plant disease resistance pipeline.

Provides configuration for JSON-structured logging of pipeline steps,
sample exclusions, and system events. Ensures logs are machine-parseable
for downstream monitoring and debugging.
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict

# Import existing exceptions to log them specifically
from .exceptions import PipelineError, EX_DATA_INTEGRITY, EX_POWER_INSUFFICIENT

# Import config for path handling
from ..config import get_artifacts_path, get_reports_path

# Constants for log levels and formats
LOG_FORMATTER = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Global logger instance
_logger: Optional[logging.Logger] = None


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON lines for structured parsing.
    Includes timestamp, level, module, message, and optional extra context.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "module": record.module,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # Attach extra context if present
        if hasattr(record, "extra_data"):
            log_obj["data"] = record.extra_data

        # Attach exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieves or creates the global logger instance with structured formatting.
    Configures handlers for both console (info+) and file (debug+) output.

    Args:
        name: The name of the logger (default: "llmXive")

    Returns:
        Configured logging.Logger instance
    """
    global _logger
    if _logger is not None and _logger.name == name:
        return _logger

    _logger = logging.getLogger(name)
    _logger.setLevel(logging.DEBUG)

    # Prevent adding handlers multiple times if called repeatedly
    if _logger.handlers:
        return _logger

    # Console Handler (stdout) - Level INFO and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(LOG_FORMATTER)
    _logger.addHandler(console_handler)

    # File Handler (artifacts/logs/pipeline.log) - Level DEBUG and above
    try:
        artifacts_dir = get_artifacts_path()
        log_dir = Path(artifacts_dir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "pipeline.log"

        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(StructuredFormatter())
        _logger.addHandler(file_handler)
    except Exception as e:
        # Fallback if artifact path is not configured yet
        _logger.warning(f"Could not initialize file logging: {e}")

    return _logger


def log_pipeline_step(step_name: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Logs a structured event for a pipeline step execution.

    Args:
        step_name: Name of the pipeline step (e.g., "preprocess", "feature_selection")
        status: Status of the step (e.g., "STARTED", "COMPLETED", "FAILED")
        details: Optional dictionary of context data (e.g., sample counts, durations)
    """
    logger = get_logger()
    log_data = {
        "event_type": "PIPELINE_STEP",
        "step": step_name,
        "status": status,
    }
    if details:
        log_data["details"] = details

    # Log as info or error based on status
    if status == "FAILED":
        logger.error("Pipeline step failed", extra={"extra_data": log_data})
    else:
        logger.info("Pipeline step event", extra={"extra_data": log_data})


def log_sample_exclusion(sample_id: str, reason: str, modality: Optional[str] = None) -> None:
    """
    Logs a sample exclusion event for audit trails.
    Automatically writes to the exclusion log file in data/processed.

    Args:
        sample_id: The unique identifier of the excluded sample
        reason: The reason for exclusion (e.g., "missing metabolite data")
        modality: The specific modality that caused exclusion (optional)
    """
    logger = get_logger()
    exclusion_data = {
        "event_type": "SAMPLE_EXCLUSION",
        "sample_id": sample_id,
        "reason": reason,
        "modality": modality,
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Log to console/file
    logger.warning(f"Sample excluded: {sample_id} - {reason}", extra={"extra_data": exclusion_data})

    # Append to exclusion log CSV
    try:
        # Determine output path based on config
        # Note: We use a relative path from data root, constructed via config if possible
        # Fallback to standard project structure if config is not fully initialized
        data_path = get_artifacts_path()
        exclusion_log_path = Path(data_path) / ".." / "data" / "processed" / "exclusion_log.csv"
        
        # Ensure parent exists
        exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)

        file_exists = exclusion_log_path.exists()

        with open(exclusion_log_path, "a", encoding="utf-8") as f:
            if not file_exists:
                # Write header
                f.write("sample_id,missing_modality,timestamp\n")
            
            # Write row (simple CSV append, no quotes for simplicity in this context)
            # Escape commas in reason if necessary, but for now assume standard strings
            f.write(f"{sample_id},{modality or 'unknown'},{exclusion_data['timestamp']}\n")

    except Exception as e:
        logger.error(f"Failed to write exclusion log to disk: {e}")


def log_error_context(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Logs an exception with structured context for debugging.

    Args:
        error: The exception instance
        context: Optional dictionary of contextual variables
    """
    logger = get_logger()
    error_data = {
        "event_type": "ERROR",
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    if context:
        error_data["context"] = context

    logger.error("Pipeline error occurred", exc_info=True, extra={"extra_data": error_data})