import logging
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs.
    Includes timestamp, level, logger name, message, and optional extra context.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_entry["data"] = record.extra_data

        return json.dumps(log_entry)

def setup_logging(
    log_dir: Optional[str] = None,
    log_level: int = logging.INFO,
    console_output: bool = True,
    file_output: bool = True
) -> None:
    """
    Configure the global logging infrastructure.
    
    Args:
        log_dir: Directory path for log files. Defaults to 'data/results'.
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG).
        console_output: Whether to stream logs to stdout.
        file_output: Whether to write logs to a file.
    
    This function configures:
    1. A file handler writing structured JSON to data/results/<timestamp>.log
    2. A console handler writing human-readable logs to stdout
    """
    # Ensure log directory exists
    if log_dir is None:
        log_dir = "data/results"
    
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Create unique log filename based on timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_path / f"pipeline_{timestamp}.log"
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Create formatter for file (Structured JSON)
    file_formatter = StructuredFormatter()
    
    # Create file handler if requested
    if file_output:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Create console handler if requested
    if console_output:
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger configured with the global settings.
    
    Args:
        name: Logger name (usually __name__).
    
    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)

def log_metric(logger: logging.Logger, metric_name: str, value: float, details: Optional[dict] = None) -> None:
    """
    Helper function to log a specific metric in a structured way.
    
    Args:
        logger: The logger instance to use.
        metric_name: Name of the metric.
        value: The metric value.
        details: Optional dictionary of additional context.
    """
    extra_data = {
        "metric_name": metric_name,
        "value": value
    }
    if details:
        extra_data.update(details)
    
    logger.info(f"Metric recorded: {metric_name} = {value}", extra={'extra_data': extra_data})

def main():
    """
    Example usage of the logging configuration.
    This function demonstrates writing logs to both console and file.
    """
    # Setup logging
    setup_logging(
        log_dir="data/results",
        log_level=logging.DEBUG,
        console_output=True,
        file_output=True
    )
    
    # Get a logger
    logger = get_logger("T008_LoggingDemo")
    
    # Log standard messages
    logger.info("Logging infrastructure initialized successfully.")
    logger.debug("This is a debug message.")
    logger.warning("This is a warning message.")
    
    # Log a structured metric
    log_metric(logger, "sample_metric", 0.95, {"source": "test", "unit": "r_value"})
    
    # Log an error with exception info
    try:
        1 / 0
    except ZeroDivisionError:
        logger.error("An error occurred during division.", exc_info=True)
    
    # Log a custom structured message
    logger.info("Pipeline phase completed", extra={'extra_data': {"phase": "setup", "status": "success"}})

if __name__ == "__main__":
    main()