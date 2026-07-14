"""
Logging configuration for the material strength prediction pipeline.

Initializes a logger that writes to:
- results/metrics.log (human-readable text format)
- results/metrics.json (structured JSON format)

JSON Schema for metrics.json:
{
  "timestamp": "ISO8601 string",
  "level": "DEBUG|INFO|WARNING|ERROR|CRITICAL",
  "module": "string",
  "message": "string",
  "extra": {
    "metric_name": "string (optional)",
    "metric_value": "number (optional)",
    "iteration": "integer (optional)"
  }
}
"""
import os
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

# Ensure the results directory exists
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

LOG_FILE_PATH = RESULTS_DIR / "metrics.log"
JSON_LOG_FILE_PATH = RESULTS_DIR / "metrics.json"

# Custom JSON formatter
class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "message": record.getMessage(),
            "extra": {}
        }

        # Include custom extra fields if present
        if hasattr(record, 'metric_name'):
            log_entry["extra"]["metric_name"] = record.metric_name
        if hasattr(record, 'metric_value'):
            log_entry["extra"]["metric_value"] = record.metric_value
        if hasattr(record, 'iteration'):
            log_entry["extra"]["iteration"] = record.iteration

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

def get_logger(name: str = "material_strength") -> logging.Logger:
    """
    Retrieves or creates a logger with dual handlers (text and JSON).
    
    Args:
        name: Logger name (default: "material_strength")
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers if already configured
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers to ensure clean state
    logger.handlers.clear()
    
    # Create file handler for text log
    file_handler = logging.FileHandler(LOG_FILE_PATH, mode='a')
    file_handler.setLevel(logging.DEBUG)
    text_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    file_handler.setFormatter(text_formatter)
    
    # Create file handler for JSON log
    json_handler = logging.FileHandler(JSON_LOG_FILE_PATH, mode='w')
    json_handler.setLevel(logging.DEBUG)
    json_handler.setFormatter(JsonFormatter())
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(json_handler)
    
    # Prevent propagation to root logger to avoid duplicate console logs
    logger.propagate = False
    
    return logger

def log_metric(
    logger: logging.Logger,
    metric_name: str,
    value: float,
    iteration: Optional[int] = None,
    level: int = logging.INFO
) -> None:
    """
    Logs a metric value with optional iteration tracking.
    
    Args:
        logger: Logger instance
        metric_name: Name of the metric
        value: Metric value
        iteration: Optional iteration number
        level: Logging level (default: INFO)
    """
    extra = {
        'metric_name': metric_name,
        'metric_value': value
    }
    if iteration is not None:
        extra['iteration'] = iteration
    
    logger.log(level, f"Metric: {metric_name} = {value}", extra=extra)

def main() -> None:
    """
    Main function to demonstrate logging configuration.
    Writes sample logs to verify functionality.
    """
    logger = get_logger()
    
    logger.info("Logging configuration initialized successfully.")
    logger.debug("Debug message for testing.")
    
    # Log sample metrics
    log_metric(logger, "loss", 0.5432, iteration=1)
    log_metric(logger, "accuracy", 0.8765, iteration=1)
    log_metric(logger, "loss", 0.4321, iteration=2)
    
    logger.info("Sample logging completed.")
    print(f"Logs written to: {LOG_FILE_PATH} and {JSON_LOG_FILE_PATH}")

if __name__ == "__main__":
    main()