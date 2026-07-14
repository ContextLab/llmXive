"""
Logging infrastructure for the molecular reactivity project.

Provides structured logging to files and a metrics logger for JSON metrics.
"""
import os
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Optional, Dict, Any
from config import get_config, ensure_directories

# Global logger instance
_logger: Optional[logging.Logger] = None
_metrics_file_path: Optional[str] = None
_metrics_data: Dict[str, Any] = {}

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure the root logger and project-specific logger.
    
    Creates structured log files in artifacts/logs/ and initializes
    the metrics file path.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured project logger instance
    """
    global _logger, _metrics_file_path
    
    if _logger is not None:
        return _logger
    
    config = get_config()
    ensure_directories()
    
    log_dir = os.path.join(config["artifacts_dir"], "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"project_{timestamp}.log"
    log_file_path = os.path.join(log_dir, log_filename)
    
    _logger = logging.getLogger("molecular_reactivity")
    _logger.setLevel(getattr(logging, log_level.upper()))
    
    if _logger.handlers:
        _logger.handlers.clear()
    
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, log_level.upper()))
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    _logger.addHandler(file_handler)
    _logger.addHandler(console_handler)
    
    _metrics_file_path = os.path.join(config["artifacts_dir"], "metrics.json")
    
    _logger.info(f"Logging initialized. Logs written to: {log_file_path}")
    _logger.info(f"Metrics will be written to: {_metrics_file_path}")
    
    return _logger

def get_logger() -> logging.Logger:
    """
    Get the configured project logger.
    
    Returns:
        The project logger instance, initializing if necessary
    """
    if _logger is None:
        return setup_logging()
    return _logger

def log_metric(metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
    """
    Log a metric value to the metrics.json file.
    
    Appends the metric to the JSON file in a structured format.
    Handles file creation and appending safely.
    
    Args:
        metric_name: Name of the metric
        value: Numeric value of the metric
        tags: Optional dictionary of key-value tags for categorization
    """
    global _metrics_file_path, _metrics_data
    
    if _metrics_file_path is None:
        config = get_config()
        ensure_directories()
        _metrics_file_path = os.path.join(config["artifacts_dir"], "metrics.json")
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "metric_name": metric_name,
        "value": value,
        "tags": tags or {}
    }
    
    try:
        if os.path.exists(_metrics_file_path):
            with open(_metrics_file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    try:
                        _metrics_data = json.loads(content)
                    except json.JSONDecodeError:
                        _metrics_data = []
        
        if not isinstance(_metrics_data, list):
            _metrics_data = []
        
        _metrics_data.append(entry)
        
        with open(_metrics_file_path, "w", encoding="utf-8") as f:
            json.dump(_metrics_data, f, indent=2)
            
        logger = get_logger()
        logger.debug(f"Metric logged: {metric_name} = {value}")
        
    except Exception as e:
        logger = get_logger()
        logger.error(f"Failed to write metric to {_metrics_file_path}: {e}")
        raise

def flush_metrics() -> None:
    """
    Ensure all metrics are written to disk.
    
    This is primarily useful in long-running processes to ensure
    metrics are persisted before exit.
    """
    logger = get_logger()
    logger.info("Metrics flushed to disk")

def get_metrics() -> list:
    """
    Retrieve all logged metrics from the metrics file.
    
    Returns:
        List of metric dictionaries
    """
    global _metrics_file_path, _metrics_data
    
    if _metrics_file_path is None or not os.path.exists(_metrics_file_path):
        return []
    
    try:
        with open(_metrics_file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except json.JSONDecodeError:
        return []

def log_execution_summary(
    task_name: str,
    start_time: datetime,
    end_time: datetime,
    success: bool,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a structured execution summary for a task.
    
    Args:
        task_name: Name of the task
        start_time: Task start time
        end_time: Task end time
        success: Whether the task completed successfully
        details: Optional dictionary of additional details
    """
    logger = get_logger()
    
    duration = (end_time - start_time).total_seconds()
    
    summary = {
        "task": task_name,
        "status": "success" if success else "failed",
        "duration_seconds": duration,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "details": details or {}
    }
    
    if success:
        logger.info(f"Task '{task_name}' completed successfully in {duration:.2f}s")
    else:
        logger.error(f"Task '{task_name}' failed after {duration:.2f}s")
    
    log_metric(
        "task_execution_duration",
        duration,
        tags={"task": task_name, "status": "success" if success else "failed"}
    )

def main():
    """
    Main entry point for testing the logging setup.
    """
    logger = setup_logging()
    
    logger.info("Logging infrastructure test started")
    
    log_metric("test_metric_1", 0.95, {"source": "test"})
    log_metric("test_metric_2", 100, {"source": "test"})
    
    logger.warning("This is a test warning")
    logger.error("This is a test error")
    
    log_execution_summary(
        "logging_test_task",
        datetime.now(),
        datetime.now(),
        True,
        {"note": "Testing logging infrastructure"}
    )
    
    logger.info("Logging infrastructure test completed")
    flush_metrics()

if __name__ == "__main__":
    main()
