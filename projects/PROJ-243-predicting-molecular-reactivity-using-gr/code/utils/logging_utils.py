import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Optional, Dict, Any
from config import get_config, ensure_directories

_logger: Optional[logging.Logger] = None
_metrics_buffer: Dict[str, Any] = {}
_metrics_file_path: Optional[str] = None

def setup_logging(script_name: Optional[str] = None) -> logging.Logger:
    """
    Configures the global logger for the project.
    
    - Creates a file handler writing to artifacts/logs/<script_name>.log
    - Creates a stream handler for stdout
    - Configures JSON formatting for the file handler if possible, 
      otherwise uses a detailed text format.
    """
    global _logger, _metrics_file_path
    
    if _logger is not None:
        return _logger

    config = get_config()
    ensure_directories()
    
    # Ensure the log directory exists
    log_dir = os.path.join(config['paths']['artifacts'], 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Determine log file path
    if script_name:
        # Clean script name to be a valid filename
        safe_name = script_name.replace('/', '_').replace('\\', '_')
        log_filename = f"{safe_name}.log"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"run_{timestamp}.log"
        
    log_file_path = os.path.join(log_dir, log_filename)
    _metrics_file_path = os.path.join(config['paths']['artifacts'], 'metrics.json')

    # Create logger
    _logger = logging.getLogger("llmXive")
    _logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates in repeated calls
    if _logger.hasHandlers():
        _logger.handlers.clear()

    # File Handler (Structured/JSON-like output for logs)
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Stream Handler (Standard console output)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    stream_handler.setFormatter(stream_formatter)

    _logger.addHandler(file_handler)
    _logger.addHandler(stream_handler)

    _logger.info(f"Logging initialized. Log file: {log_file_path}")
    _logger.info(f"Metrics file path: {_metrics_file_path}")
    
    # Initialize metrics file if it doesn't exist
    if not os.path.exists(_metrics_file_path):
        with open(_metrics_file_path, 'w') as f:
            json.dump({}, f, indent=2)

    return _logger

def get_logger() -> logging.Logger:
    """Returns the configured logger. Initializes if necessary."""
    if _logger is None:
        return setup_logging()
    return _logger

def log_metric(key: str, value: Any, step: Optional[int] = None) -> None:
    """
    Appends a metric to the global metrics dictionary and writes to artifacts/metrics.json.
    This function is thread-safe for simple appends but assumes single-process usage for the file write.
    """
    global _metrics_buffer, _metrics_file_path
    
    if _metrics_file_path is None:
        # Fallback if logging wasn't fully initialized via setup_logging
        config = get_config()
        _metrics_file_path = os.path.join(config['paths']['artifacts'], 'metrics.json')
    
    timestamp = datetime.now().isoformat()
    
    metric_entry = {
        "key": key,
        "value": value,
        "timestamp": timestamp,
        "step": step
    }
    
    # Load existing metrics
    try:
        if os.path.exists(_metrics_file_path):
            with open(_metrics_file_path, 'r') as f:
                try:
                    current_metrics = json.load(f)
                except json.JSONDecodeError:
                    current_metrics = {}
        else:
            current_metrics = {}
    except Exception as e:
        get_logger().warning(f"Failed to read metrics file: {e}. Creating new structure.")
        current_metrics = {}

    if key not in current_metrics:
        current_metrics[key] = []
    
    current_metrics[key].append(metric_entry)
    
    # Write back to file
    try:
        with open(_metrics_file_path, 'w') as f:
            json.dump(current_metrics, f, indent=2)
    except Exception as e:
        get_logger().error(f"Failed to write metrics to {_metrics_file_path}: {e}")

def flush_metrics() -> None:
    """
    Ensures all metrics are written to disk. 
    In this implementation, metrics are written immediately, so this is a no-op 
    unless we implement a buffering strategy later.
    """
    pass

def get_metrics() -> Dict[str, Any]:
    """Reads the current metrics from the JSON file."""
    if _metrics_file_path is None:
        return {}
    if not os.path.exists(_metrics_file_path):
        return {}
    try:
        with open(_metrics_file_path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def log_execution_summary(script_name: str, status: str, duration: float, metrics_summary: Optional[Dict] = None) -> None:
    """Logs a structured summary of the script execution."""
    logger = get_logger()
    logger.info(f"--- Execution Summary for {script_name} ---")
    logger.info(f"Status: {status}")
    logger.info(f"Duration: {duration:.2f} seconds")
    if metrics_summary:
        logger.info(f"Key Metrics: {metrics_summary}")
    logger.info("-------------------------------------------")

def main():
    """
    Main entry point for testing the logging setup directly.
    """
    logger = setup_logging("test_logging")
    logger.info("Test log message from main.")
    log_metric("test_metric", 123.45)
    log_metric("test_metric", 678.90, step=1)
    
    logger.info("Verifying metrics file...")
    metrics = get_metrics()
    logger.info(f"Retrieved metrics: {metrics}")

if __name__ == "__main__":
    main()
