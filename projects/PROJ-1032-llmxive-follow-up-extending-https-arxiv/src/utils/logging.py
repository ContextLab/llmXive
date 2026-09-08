import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

# Ensure the output directory exists
LOG_OUTPUT_DIR = "data/processed"
os.makedirs(LOG_OUTPUT_DIR, exist_ok=True)

class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Attach extra fields if present
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        # Attach exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

def get_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Configure and return a logger that writes JSON to file and stdout.

    Args:
        name: Logger name (usually __name__).
        log_file: Relative filename for the log output (e.g., 'training_run.json').
                 If None, defaults to '{name}_{timestamp}.json'.
        level: Logging level.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    # Determine log file path
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"{name.replace('.', '_')}_{timestamp}.json"

    log_path = os.path.join(LOG_OUTPUT_DIR, log_file)

    # File handler with JSON formatting
    file_handler = logging.FileHandler(log_path, mode='a')
    file_handler.setLevel(level)
    file_handler.setFormatter(JsonFormatter())

    # Console handler for immediate feedback (optional, but useful)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)  # Only warn+ to stdout
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def log_metric(
    logger: logging.Logger,
    metric_name: str,
    value: float,
    step: int,
    **kwargs: Any,
) -> None:
    """
    Helper to log a specific metric as structured data.

    Args:
        logger: The configured logger.
        metric_name: Name of the metric (e.g., 'reward', 'gradient_norm').
        value: The numeric value.
        step: The current training step.
        **kwargs: Additional context data to include in the log.
    """
    extra_data = {
        "metric_name": metric_name,
        "value": value,
        "step": step,
        **kwargs,
    }
    logger.info(
        f"Metric: {metric_name} = {value} at step {step}",
        extra={"extra_data": extra_data},
    )

def log_event(
    logger: logging.Logger,
    event_type: str,
    description: str,
    **kwargs: Any,
) -> None:
    """
    Helper to log a significant event (e.g., divergence, model load).

    Args:
        logger: The configured logger.
        event_type: Type of event (e.g., 'DIVERGENCE_DETECTED', 'MODEL_LOADED').
        description: Human-readable description.
        **kwargs: Additional context data.
    """
    extra_data = {
        "event_type": event_type,
        **kwargs,
    }
    logger.info(
        f"Event: {event_type} - {description}",
        extra={"extra_data": extra_data},
    )
