"""
Logging configuration for llmXive project.
Provides file rotation, JSON logging for metrics, and standard loggers.
"""
import logging
import logging.handlers
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, Union
import datetime

# Ensure the logs directory exists at the project root
LOG_DIR = Path(__file__).resolve().parent.parent.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON lines."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Include extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data)

class MetricsHandler(logging.Handler):
    """
    Specialized handler for metrics logging.
    Writes metric events to a dedicated JSON file for easy parsing.
    """
    
    def __init__(self, metrics_file: Optional[Union[str, Path]] = None):
        super().__init__()
        if metrics_file is None:
            metrics_file = LOG_DIR / "metrics.jsonl"
        self.metrics_file = Path(metrics_file)
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self.setFormatter(JSONFormatter())
    
    def emit(self, record: logging.LogRecord):
        try:
            log_entry = json.loads(self.format(record))
            with open(self.metrics_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            self.handleError(record)

def get_logger(
    name: str,
    log_level: int = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    metrics_file: Optional[Union[str, Path]] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Create and configure a logger with file rotation and optional JSON metrics.
    
    Args:
        name: Logger name (usually __name__ of the module)
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Path to the log file. If None, uses default location.
        metrics_file: Path to the metrics JSONL file. If None, uses default.
        max_bytes: Maximum size of log file before rotation (bytes)
        backup_count: Number of backup files to keep
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file is None:
        log_file = LOG_DIR / f"{name}.log"
    log_file = Path(log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Metrics handler for JSON metrics
    if metrics_file is not None:
        metrics_handler = MetricsHandler(metrics_file)
        metrics_handler.setLevel(logging.INFO)
        logger.addHandler(metrics_handler)
    
    return logger

def log_metric(
    logger: logging.Logger,
    metric_name: str,
    metric_value: Union[int, float, str],
    **kwargs
) -> None:
    """
    Log a metric value to both the standard log and the metrics file.
    
    Args:
        logger: Logger instance
        metric_name: Name of the metric
        metric_value: Value of the metric
        **kwargs: Additional context to include in the log
    """
    extra_data = {"metric_name": metric_name, "metric_value": metric_value}
    extra_data.update(kwargs)
    
    record = logger.makeRecord(
        logger.name,
        logging.INFO,
        "",
        0,
        f"METRIC: {metric_name} = {metric_value}",
        (),
        None
    )
    record.extra_data = extra_data
    logger.handle(record)

def log_metric_value(
    logger: logging.Logger,
    metric_name: str,
    value: Union[int, float],
    epoch: Optional[int] = None,
    step: Optional[int] = None
) -> None:
    """
    Convenience function to log a metric with epoch/step context.
    
    Args:
        logger: Logger instance
        metric_name: Name of the metric
        value: Metric value
        epoch: Current epoch number (optional)
        step: Current step number (optional)
    """
    context = {}
    if epoch is not None:
        context["epoch"] = epoch
    if step is not None:
        context["step"] = step
    
    log_metric(logger, metric_name, value, **context)

def setup_default_loggers(
    project_root: Optional[Union[str, Path]] = None,
    log_level: int = logging.INFO
) -> Dict[str, logging.Logger]:
    """
    Set up default loggers for the entire project.
    
    Args:
        project_root: Root directory of the project. If None, uses parent of this file.
        log_level: Default logging level
        
    Returns:
        Dictionary of logger instances
    """
    if project_root is None:
        project_root = Path(__file__).resolve().parent.parent.parent.parent
    project_root = Path(project_root)
    
    # Update LOG_DIR if needed
    global LOG_DIR
    LOG_DIR = project_root / "logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    loggers = {}
    
    # Common loggers
    for name in ["root", "generation", "filtering", "training", "evaluation", "utils"]:
        loggers[name] = get_logger(
            f"llmXive.{name}",
            log_level=log_level,
            metrics_file=LOG_DIR / "metrics.jsonl" if name == "root" else None
        )
    
    return loggers

# Convenience functions for quick logging
_default_logger = None

def get_default_logger() -> logging.Logger:
    """Get or create the default logger."""
    global _default_logger
    if _default_logger is None:
        _default_logger = get_logger("llmXive")
    return _default_logger

def info(msg: str, *args, **kwargs):
    get_default_logger().info(msg, *args, **kwargs)

def debug(msg: str, *args, **kwargs):
    get_default_logger().debug(msg, *args, **kwargs)

def warning(msg: str, *args, **kwargs):
    get_default_logger().warning(msg, *args, **kwargs)

def error(msg: str, *args, **kwargs):
    get_default_logger().error(msg, *args, **kwargs)

def critical(msg: str, *args, **kwargs):
    get_default_logger().critical(msg, *args, **kwargs)

def main():
    """Test the logging configuration."""
    logger = get_logger("test_logger", log_level=logging.DEBUG)
    
    logger.info("Test info message")
    logger.debug("Test debug message")
    logger.warning("Test warning message")
    
    log_metric(logger, "accuracy", 0.95, epoch=1, step=100)
    log_metric_value(logger, "loss", 0.05, epoch=1, step=100)
    
    print(f"Logs written to: {LOG_DIR}")

if __name__ == "__main__":
    main()
