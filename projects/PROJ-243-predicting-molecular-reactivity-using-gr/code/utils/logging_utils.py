import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any, Optional
from config import get_config, ensure_directories

# Global storage for metrics during a script run
_metrics_buffer: Dict[str, Any] = {}
_logger: Optional[logging.Logger] = None

def setup_logging(log_file: Optional[str] = None, log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure the project logging infrastructure.
    
    Creates a logger that writes to:
    1. Console (stdout) with a specific format.
    2. A rotating file handler in artifacts/logs/ if log_file is provided.
    
    Args:
        log_file: Relative path to the log file (e.g., 'artifacts/logs/run.log').
        log_level: Logging level (default INFO).
        
    Returns:
        The configured logger instance.
    """
    global _logger
    
    if _logger is not None:
        return _logger

    logger = logging.getLogger("llmXive")
    logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates in repeated runs
    logger.handlers.clear()

    # 1. Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 2. File Handler (if specified)
    if log_file:
        config = get_config()
        # Ensure the directory exists
        ensure_directories([os.path.dirname(os.path.abspath(log_file))])
        
        abs_log_path = os.path.abspath(log_file)
        file_handler = logging.handlers.RotatingFileHandler(
            abs_log_path,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    _logger = logger
    return logger

def get_logger() -> logging.Logger:
    """Retrieve the configured logger. Initializes with defaults if not set."""
    if _logger is None:
        return setup_logging()
    return _logger

def log_metric(key: str, value: Any, step: Optional[int] = None) -> None:
    """
    Record a metric to the in-memory buffer for later flushing to disk.
    
    Args:
        key: Metric name.
        value: Metric value.
        step: Optional step/epoch number.
    """
    global _metrics_buffer
    timestamp = datetime.now().isoformat()
    entry = {"value": value, "timestamp": timestamp}
    if step is not None:
        entry["step"] = step
    
    if key not in _metrics_buffer:
        _metrics_buffer[key] = []
    _metrics_buffer[key].append(entry)

def get_metrics() -> Dict[str, Any]:
    """Return the current metrics buffer."""
    return _metrics_buffer.copy()

def flush_metrics(output_path: str) -> None:
    """
    Flush the in-memory metrics buffer to a JSON file.
    
    Args:
        output_path: Absolute or relative path to the metrics JSON file.
    """
    global _metrics_buffer
    
    if not _metrics_buffer:
        return

    config = get_config()
    ensure_directories([os.path.dirname(os.path.abspath(output_path))])
    
    abs_path = os.path.abspath(output_path)
    
    # Load existing if exists to append/update, otherwise start fresh
    existing_data = {}
    if os.path.exists(abs_path):
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing_data = {}

    # Update with current run's metrics
    for key, entries in _metrics_buffer.items():
        if key not in existing_data:
            existing_data[key] = []
        existing_data[key].extend(entries)
    
    # Write back
    with open(abs_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2)
    
    # Clear buffer after flush
    _metrics_buffer = {}

def log_execution_summary(logger: logging.Logger, duration_seconds: float, success: bool) -> None:
    """
    Log a final execution summary line.
    
    Args:
        logger: The logger instance.
        duration_seconds: Total runtime.
        success: Whether the script completed without exception.
    """
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"Execution Summary: Status={status}, Duration={duration_seconds:.2f}s")
    
    # Also log to metrics if we have data
    if _metrics_buffer:
        flush_metrics("artifacts/metrics.json")

def main():
    """
    Entry point for testing the logging setup directly.
    """
    logger = setup_logging(log_file="artifacts/logs/test_run.log")
    logger.info("Logging infrastructure initialized.")
    log_metric("test_metric", 1.23, step=1)
    flush_metrics("artifacts/metrics.json")
    log_execution_summary(logger, 0.001, True)
    print("Logging test completed. Check artifacts/logs/ and artifacts/metrics.json")

if __name__ == "__main__":
    main()
