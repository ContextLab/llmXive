import logging
import logging.handlers
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, Union

# Constants for log paths relative to project root
LOG_DIR = Path("data/logs")
LOG_FILE_NAME = "pipeline.log"
METRICS_FILE_NAME = "metrics.jsonl"
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON lines.
    Includes standard fields plus extra context if available.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class MetricsHandler(logging.Handler):
    """
    A logging handler that writes specific metric logs to a JSONL file.
    Expects log messages to be JSON-serializable dictionaries or objects
    with a __dict__ attribute, or a string that is parsed as JSON.
    """
    def __init__(self, metrics_path: Path):
        super().__init__()
        self.metrics_path = metrics_path
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
        # Set formatter to just output the message as is (assuming it's JSON)
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = record.getMessage()
            # If the message is already a dict (passed via extra or directly), serialize it
            if isinstance(record.msg, dict):
                log_entry = record.msg
                log_entry["timestamp"] = self.formatTime(record)
                log_entry["level"] = record.levelname
                log_entry["metric_name"] = getattr(record, "metric_name", "unknown")
                with open(self.metrics_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
            elif isinstance(msg, str):
                # Try to parse as JSON if it looks like one, otherwise just dump the string
                try:
                    parsed = json.loads(msg)
                    parsed["timestamp"] = self.formatTime(record)
                    parsed["level"] = record.levelname
                    with open(self.metrics_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(parsed) + "\n")
                except json.JSONDecodeError:
                    # Fallback: treat as a simple string metric
                    entry = {
                        "timestamp": self.formatTime(record),
                        "level": record.levelname,
                        "message": msg
                    }
                    with open(self.metrics_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(entry) + "\n")
        except Exception:
            self.handleError(record)


def get_logger(
    name: str,
    log_dir: Optional[Path] = None,
    metrics_path: Optional[Path] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Configures and returns a logger with file rotation and optional JSON metrics handler.
    
    Args:
        name: Logger name (usually __name__)
        log_dir: Directory for log files (defaults to LOG_DIR)
        metrics_path: Path for JSONL metrics file (defaults to LOG_DIR / METRICS_FILE_NAME)
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    base_dir = log_dir or LOG_DIR
    base_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = base_dir / LOG_FILE_NAME
    metrics_file = metrics_path or (base_dir / METRICS_FILE_NAME)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    
    # JSON metrics handler
    json_handler = MetricsHandler(metrics_file)
    json_handler.setLevel(logging.INFO)
    json_handler.setFormatter(JSONFormatter())

    logger.addHandler(file_handler)
    logger.addHandler(json_handler)
    
    return logger


def log_metric(
    logger: logging.Logger,
    metric_name: str,
    value: Union[float, int, Dict[str, Any]],
    **kwargs
) -> None:
    """
    Logs a metric value to the JSON metrics file.
    
    Args:
        logger: The logger instance
        metric_name: Name of the metric
        value: The metric value (float, int, or dict of values)
        **kwargs: Additional context to include
    """
    if isinstance(value, (float, int)):
        payload = {"metric_name": metric_name, "value": value}
    else:
        payload = {"metric_name": metric_name, **value}
    
    payload.update(kwargs)
    logger.info(payload, extra={"metric_name": metric_name})


def log_metric_value(
    logger: logging.Logger,
    metric_name: str,
    value: Union[float, int],
    **kwargs
) -> None:
    """
    Convenience wrapper for log_metric with a single numeric value.
    """
    log_metric(logger, metric_name, value, **kwargs)


def setup_default_loggers() -> None:
    """
    Initializes the root logger with a console handler for the project.
    """
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        root_logger.addHandler(console_handler)
        root_logger.setLevel(logging.INFO)


def get_default_logger() -> logging.Logger:
    """
    Returns the default project logger.
    """
    setup_default_loggers()
    return logging.getLogger("llmxive")


# Convenience functions for quick logging
def info(msg: str, *args, **kwargs) -> None:
    get_default_logger().info(msg, *args, **kwargs)


def debug(msg: str, *args, **kwargs) -> None:
    get_default_logger().debug(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs) -> None:
    get_default_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs) -> None:
    get_default_logger().error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs) -> None:
    get_default_logger().critical(msg, *args, **kwargs)
