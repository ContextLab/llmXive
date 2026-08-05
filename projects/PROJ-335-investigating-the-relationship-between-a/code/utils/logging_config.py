import logging
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs JSON-structured logs.
    Includes timestamp, level, logger name, message, and optional extra fields.
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
        
        # Include exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Include extra fields if present
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
        
        return json.dumps(log_entry)

def setup_logging(
    log_file_name: str = "pipeline.log",
    log_dir: str = "data/results",
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG
) -> logging.Logger:
    """
    Configure the global logging infrastructure.
    
    Sets up:
    1. A file handler writing structured JSON logs to data/results/<log_file_name>.
    2. A console handler writing human-readable (or JSON if preferred) logs to stdout.
    
    Args:
        log_file_name: Name of the log file in data/results.
        log_dir: Directory to store logs (default: data/results).
        console_level: Minimum level for console output.
        file_level: Minimum level for file output.
        
    Returns:
        The root logger instance configured with these handlers.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG) # Capture everything, filters on handlers
    
    # Clear existing handlers to avoid duplicates on re-runs
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    # Ensure output directory exists
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    log_file_path = log_path / log_file_name
    
    # --- File Handler (Structured JSON) ---
    file_handler = logging.FileHandler(log_file_path, mode='a')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(StructuredFormatter())
    
    # --- Console Handler (Human Readable) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    
    # Standard formatter for console for readability
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log startup confirmation
    root_logger.info(f"Logging initialized. File: {log_file_path}, Console: {console_level}")
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a logger by name.
    Assumes setup_logging() has been called.
    """
    return logging.getLogger(name)

def log_metric(logger: logging.Logger, metric_name: str, value: float, context: Optional[dict] = None):
    """
    Helper to log a metric in a structured way.
    
    Args:
        logger: The logger instance.
        metric_name: Name of the metric (e.g., 'alpha_power_mean').
        value: The numeric value.
        context: Optional dict of extra context (e.g., subject_id, electrode).
    """
    extra_data = {"metric_name": metric_name, "value": value}
    if context:
        extra_data.update(context)
    
    # Create a log record with extra data
    # We use a custom attribute to pass data to StructuredFormatter
    logger.info(f"Metric: {metric_name} = {value}", extra={"extra_data": extra_data})

def main():
    """
    Demonstration of logging configuration.
    Runs when this file is executed directly.
    """
    # Setup logging
    logger = setup_logging(log_file_name="test_run.log", log_dir="data/results")
    
    # Get a module-specific logger
    module_logger = get_logger("T008_Demo")
    
    module_logger.info("Starting logging demonstration.")
    module_logger.warning("This is a warning message.")
    module_logger.error("This is an error message.")
    
    # Log a metric
    log_metric(module_logger, "test_metric", 0.85, {"subject": "sub-01", "condition": "high_load"})
    
    # Simulate an exception
    try:
        raise ValueError("Simulated error for logging test")
    except ValueError:
        module_logger.exception("Caught an exception during demo.")
    
    print(f"\nLogs written to: data/results/test_run.log")
    print("Check console output above and file output below.")

if __name__ == "__main__":
    main()