import os
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import get_config

# Global state for metrics accumulation
_metrics_buffer: List[Dict[str, Any]] = []
_metrics_file_path: Optional[str] = None
_logger: Optional[logging.Logger] = None

def setup_logging(
    log_dir: str = "artifacts/logs",
    log_file_name: str = "pipeline.log",
    metrics_file_name: str = "metrics.json",
    level: int = logging.INFO
) -> logging.Logger:
    """
    Initialize the logging infrastructure.
    
    Creates the log directory if it doesn't exist.
    Configures a root logger with:
    1. A rotating file handler writing to artifacts/logs/pipeline.log
    2. A console handler for immediate feedback
    
    Sets up the global metrics file path for subsequent log_metric calls.
    
    Args:
        log_dir: Directory for log files.
        log_file_name: Name of the log file.
        metrics_file_name: Name of the metrics JSON file.
        level: Logging level (e.g., logging.INFO).
        
    Returns:
        The configured root logger.
    """
    global _metrics_file_path, _logger

    # Ensure directories exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Setup metrics file path
    _metrics_file_path = os.path.join(log_dir, metrics_file_name)
    
    # Clear existing handlers to avoid duplicates if called multiple times
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    root_logger.setLevel(level)

    # File Handler (Rotating)
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, log_file_name),
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # Formatter: ISO8601 timestamp, level, logger name, message
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    _logger = root_logger
    _logger.info("Logging infrastructure initialized.")
    _logger.info(f"Log file: {os.path.join(log_dir, log_file_name)}")
    _logger.info(f"Metrics file: {_metrics_file_path}")

    # Initialize empty metrics file if it doesn't exist
    if not os.path.exists(_metrics_file_path):
        with open(_metrics_file_path, 'w') as f:
            json.dump([], f)

    return _logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance. If name is provided, returns a child logger.
    Otherwise returns the root logger configured by setup_logging.
    """
    if _logger is None:
        # Fallback if setup_logging wasn't called explicitly
        setup_logging()
    
    if name:
        return logging.getLogger(name)
    return _logger

def log_metric(
    metric_name: str,
    value: Any,
    stage: str = "unknown",
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a metric to the global metrics buffer and immediately flush to disk.
    
    Args:
        metric_name: Name of the metric (e.g., 'mse', 'accuracy').
        value: The numeric or string value of the metric.
        stage: The pipeline stage where this metric was recorded.
        details: Optional dictionary of additional context.
    """
    if _metrics_file_path is None:
        # Fallback: try to setup logging if not done
        setup_logging()
    
    timestamp = datetime.utcnow().isoformat()
    
    entry = {
        "timestamp": timestamp,
        "metric_name": metric_name,
        "value": value,
        "stage": stage,
        "details": details or {}
    }
    
    # Append to buffer
    _metrics_buffer.append(entry)
    
    # Immediate flush to ensure data persistence on crash
    flush_metrics()

    # Also log to the text log for immediate visibility
    logger = get_logger()
    logger.info(f"METRIC | {stage} | {metric_name} = {value}")

def flush_metrics() -> None:
    """
    Write the accumulated metrics buffer to the JSON file.
    This clears the buffer and overwrites the file with current state.
    """
    if _metrics_file_path is None:
        return

    try:
        # Read existing content to append safely (avoid overwriting if race condition)
        # In a single-threaded script, we can just write the buffer, 
        # but reading first is safer for concurrent runs.
        existing_data = []
        if os.path.exists(_metrics_file_path):
            try:
                with open(_metrics_file_path, 'r') as f:
                    existing_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                existing_data = []
        
        # Combine existing with new buffer
        combined = existing_data + _metrics_buffer
        
        with open(_metrics_file_path, 'w') as f:
            json.dump(combined, f, indent=2)
        
        _metrics_buffer.clear()
    except IOError as e:
        logging.error(f"Failed to flush metrics to {_metrics_file_path}: {e}")

def get_metrics() -> List[Dict[str, Any]]:
    """
    Read all metrics from the metrics file.
    
    Returns:
        List of metric dictionaries.
    """
    if _metrics_file_path is None or not os.path.exists(_metrics_file_path):
        return []
    
    try:
        with open(_metrics_file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def log_execution_summary(
    stage: str,
    success: bool,
    duration_seconds: float,
    metrics: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a structured summary of a pipeline stage execution.
    
    Args:
        stage: Name of the stage.
        success: Boolean indicating success.
        duration_seconds: Time taken in seconds.
        metrics: Optional dict of specific metrics for this run.
    """
    logger = get_logger()
    
    status = "SUCCESS" if success else "FAILURE"
    logger.info(f"EXECUTION_SUMMARY | Stage: {stage} | Status: {status} | Duration: {duration_seconds:.2f}s")
    
    if metrics:
        for key, val in metrics.items():
            log_metric(key, val, stage=stage, details={"summary": True})

def main():
    """
    Simple test entry point to demonstrate logging functionality.
    """
    logger = setup_logging()
    logger.info("Testing logging infrastructure...")
    
    log_metric("test_metric", 42.5, stage="test", details={"unit": "count"})
    log_metric("test_status", "completed", stage="test")
    
    log_execution_summary("demo_stage", True, 1.23, {"accuracy": 0.95})
    
    logger.info("Logging test complete. Check artifacts/logs/ for output.")

if __name__ == "__main__":
    main()
