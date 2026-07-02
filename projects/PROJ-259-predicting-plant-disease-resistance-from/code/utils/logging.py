"""
Structured logging utilities for the plant disease resistance pipeline.

Provides a centralized logging configuration that outputs JSON-formatted
logs to stdout and files, with support for pipeline step tracking and
sample exclusion logging as required by FR-001.
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from config import get_path, Config


# Custom log format for structured output
LOG_FORMATTER = logging.Formatter(
  fmt='{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
      '"module": "%(name)s", "message": "%(message)s"}',
  datefmt='%Y-%m-%dT%H:%M:%S'
)

# Cache for configured logger to avoid re-initialization
_logger: Optional[logging.Logger] = None
_exclusion_handler: Optional[logging.FileHandler] = None


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs JSON-structured log messages."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }

        # Include extra fields if present
        if hasattr(record, 'step'):
            log_data['step'] = record.step
        if hasattr(record, 'sample_id'):
            log_data['sample_id'] = record.sample_id
        if hasattr(record, 'missing_modality'):
            log_data['missing_modality'] = record.missing_modality
        if hasattr(record, 'reason'):
            log_data['reason'] = record.reason
        if hasattr(record, 'exc_info') and record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def get_logger(name: str = "plant_pipeline") -> logging.Logger:
    """
    Get or create a configured logger instance.

    Args:
        name: Logger name, typically the module name (__name__)

    Returns:
        Configured logging.Logger instance
    """
    global _logger

    if _logger is not None:
        return logging.getLogger(name)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Console handler (JSON format)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(console_handler)

    # File handler for general pipeline logs
    log_dir = get_path(Config.LOG_DIR, "artifacts/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(file_handler)

    _logger = logging.getLogger(name)
    return _logger


def setup_exclusion_logger() -> logging.Handler:
    """
    Setup a dedicated file handler for logging sample exclusions.

    This handler writes to `data/processed/exclusion_log.csv` as required
    by FR-001, capturing sample_id, missing_modality, and timestamp.

    Returns:
        The configured FileHandler instance (to be added to a logger)
    """
    global _exclusion_handler

    if _exclusion_handler is not None:
        return _exclusion_handler

    data_dir = get_path(Config.DATA_PROCESSED_DIR, "data/processed")
    data_dir.mkdir(parents=True, exist_ok=True)
    exclusion_file = data_dir / "exclusion_log.csv"

    # Create CSV header if file doesn't exist
    if not exclusion_file.exists():
        with open(exclusion_file, 'w') as f:
            f.write("sample_id,missing_modality,timestamp\n")

    # Use a custom handler that appends to CSV
    class CsvExclusionHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            sample_id = getattr(record, 'sample_id', 'UNKNOWN')
            missing_modality = getattr(record, 'missing_modality', 'UNKNOWN')
            timestamp = datetime.now().isoformat()
            line = f"{sample_id},{missing_modality},{timestamp}\n"
            with open(exclusion_file, 'a') as f:
                f.write(line)

    _exclusion_handler = CsvExclusionHandler()
    _exclusion_handler.setLevel(logging.INFO)
    return _exclusion_handler


def log_pipeline_step(step_name: str, status: str = "STARTED", details: Optional[Dict] = None) -> None:
    """
    Log a pipeline step event.

    Args:
        step_name: Name of the pipeline step (e.g., "data_preprocessing", "model_training")
        status: Status of the step (STARTED, COMPLETED, FAILED)
        details: Optional dictionary of step-specific details
    """
    logger = get_logger()
    extra = {"step": step_name}
    if details:
        for k, v in details.items():
            extra[k] = v
    logger.info(f"Pipeline step: {step_name} - {status}", extra=extra)


def log_sample_exclusion(sample_id: str, missing_modality: str, reason: Optional[str] = None) -> None:
    """
    Log a sample exclusion event to the dedicated exclusion log.

    Args:
        sample_id: The ID of the excluded sample
        missing_modality: The modality that was missing (e.g., "SNP", "metabolite")
        reason: Optional reason for exclusion
    """
    logger = get_logger()
    exclusion_handler = setup_exclusion_logger()

    extra = {
        "sample_id": sample_id,
        "missing_modality": missing_modality,
        "reason": reason or "Missing modality data"
    }

    # Log to both general logger and exclusion handler
    logger.warning(f"Excluding sample {sample_id}: {extra['reason']}", extra=extra)

    # Directly emit to CSV handler
    exclusion_handler.emit(logging.LogRecord(
        name="exclusion",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="",
        args=(),
        exc_info=None
    ))


def log_metric(name: str, value: float, step: str = "") -> None:
    """
    Log a performance metric.

    Args:
        name: Name of the metric (e.g., "accuracy", "auc")
        value: Numeric value of the metric
        step: Optional step context
    """
    logger = get_logger()
    extra = {"metric_name": name, "metric_value": value}
    if step:
        extra["step"] = step
    logger.info(f"Metric recorded: {name} = {value}", extra=extra)