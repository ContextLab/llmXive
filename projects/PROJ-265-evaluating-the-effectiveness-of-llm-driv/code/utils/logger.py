"""
Structured JSON logging utilities for the pipeline.
"""
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "stage"):
            log_data["stage"] = record.stage
        if hasattr(record, "duration"):
            log_data["duration_seconds"] = record.duration
        if hasattr(record, "metrics") and record.metrics:
            log_data["metrics"] = record.metrics
        if hasattr(record, "exclusion_reason"):
            log_data["exclusion_reason"] = record.exclusion_reason
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger with JSON formatting.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    # File handler (optional, can be configured via env)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "pipeline.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    return logger

def log_stage_start(logger: logging.Logger, stage_name: str) -> None:
    """Log the start of a pipeline stage."""
    logger.info(f"Starting stage: {stage_name}", extra={"stage": stage_name})

def log_stage_complete(logger: logging.Logger, stage_name: str, metrics: Optional[dict] = None) -> None:
    """Log the successful completion of a pipeline stage."""
    msg = f"Completed stage: {stage_name}"
    if metrics:
        msg += f" | Metrics: {json.dumps(metrics)}"
    logger.info(msg, extra={"stage": stage_name, "metrics": metrics})

def log_stage_error(logger: logging.Logger, stage_name: str, error: str) -> None:
    """Log an error during a pipeline stage."""
    logger.error(f"Error in stage {stage_name}: {error}", extra={"stage": stage_name})

def log_stage_exclusion(
    logger: logging.Logger,
    stage_name: str,
    reason: str,
    item_id: Optional[str] = None,
    details: Optional[dict] = None
) -> None:
    """
    Log an exclusion event with a specific reason (syntax error, import failure, drift).

    Args:
        logger: The logger instance to use.
        stage_name: The pipeline stage where exclusion occurred.
        reason: The specific reason for exclusion (e.g., 'syntax_error', 'import_failure', 'equivalence_drift').
        item_id: Optional identifier for the excluded item (e.g., function name, file path).
        details: Optional dictionary of additional context (e.g., error message, stratum).
    """
    extra_data = {
        "stage": stage_name,
        "exclusion_reason": reason,
        "item_id": item_id,
        "details": details
    }
    msg = f"Excluded item from {stage_name}: {reason}"
    if item_id:
        msg += f" (ID: {item_id})"
    logger.warning(msg, extra=extra_data)

def log_message(logger: logging.Logger, level: str, message: str, **kwargs) -> None:
    """Log a generic message with optional extra context."""
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(message, extra=kwargs)

class StageTimer:
    """Context manager to time stage execution."""

    def __init__(self, logger: logging.Logger, stage_name: str):
        self.logger = logger
        self.stage_name = stage_name
        self.start_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        log_stage_start(self.logger, self.stage_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if exc_type:
            log_stage_error(self.logger, self.stage_name, str(exc_val))
        else:
            log_stage_complete(self.logger, self.stage_name, {"duration_seconds": duration})
        return False

def main():
    """Demo usage of the logger with exclusion logging."""
    logger = get_logger("demo")
    with StageTimer(logger, "demo_stage"):
        time.sleep(0.01)
        logger.info("Demo message")
        # Demonstrate exclusion logging
        log_stage_exclusion(
            logger,
            "demo_stage",
            "syntax_error",
            item_id="test_func_1",
            details={"error": "unexpected EOF while parsing"}
        )
        log_stage_exclusion(
            logger,
            "demo_stage",
            "import_failure",
            item_id="test_func_2",
            details={"missing_module": "pandas"}
        )
        log_stage_exclusion(
            logger,
            "demo_stage",
            "equivalence_drift",
            item_id="test_func_3",
            details={"drift_type": "output_mismatch"}
        )

if __name__ == "__main__":
    main()