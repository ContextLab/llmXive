"""
Logging utilities for the llmXive automated science pipeline.
Provides structured logging to files and JSON metric tracking.
"""
import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Optional, Dict, Any
from config import get_config, ensure_directories

# Global logger instance
_logger: Optional[logging.Logger] = None
_metrics: Dict[str, Any] = {}
_metrics_file_path: Optional[str] = None

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure the root logger and project-specific logger.
    Writes structured logs to artifacts/logs/ with timestamps.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    global _logger, _metrics_file_path
    
    config = get_config()
    ensure_directories()
    
    # Set root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    # Create project logger
    _logger = logging.getLogger("llmXive")
    _logger.setLevel(log_level)
    
    # Create log directory
    log_dir = os.path.join(config["paths"]["artifacts"], "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"run_{timestamp}.log"
    log_file_path = os.path.join(log_dir, log_filename)
    
    # File handler with rotating file handler (max 10MB, 5 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    
    # JSON formatter for structured logs
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            if hasattr(record, 'extra_data'):
                log_data.update(record.extra_data)
            return json.dumps(log_data)
    
    file_handler.setFormatter(JsonFormatter())
    _logger.addHandler(file_handler)
    
    # Console handler for debugging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    _logger.addHandler(console_handler)
    
    # Initialize metrics file path
    _metrics_file_path = os.path.join(config["paths"]["artifacts"], "metrics.json")
    
    # Initialize metrics file if it doesn't exist
    if not os.path.exists(_metrics_file_path):
        with open(_metrics_file_path, 'w') as f:
            json.dump({"metrics": [], "runs": []}, f, indent=2)
    
    _logger.info(f"Logging initialized. Log file: {log_file_path}")
    _logger.info(f"Metrics file: {_metrics_file_path}")
    
    return _logger

def get_logger() -> logging.Logger:
    """
    Get the configured project logger.
    Raises RuntimeError if logging hasn't been initialized.
    """
    if _logger is None:
        raise RuntimeError("Logging not initialized. Call setup_logging() first.")
    return _logger

def log_metric(name: str, value: Any, run_id: Optional[str] = None) -> None:
    """
    Log a metric to the JSON metrics file.
    
    Args:
        name: Metric name
        value: Metric value (must be JSON serializable)
        run_id: Optional run identifier
    """
    global _metrics, _metrics_file_path
    
    if _metrics_file_path is None:
        raise RuntimeError("Metrics file not initialized. Call setup_logging() first.")
    
    timestamp = datetime.now().isoformat()
    metric_entry = {
        "name": name,
        "value": value,
        "timestamp": timestamp,
        "run_id": run_id or "default"
    }
    
    _metrics[name] = value
    
    # Read existing metrics
    try:
        with open(_metrics_file_path, 'r') as f:
            metrics_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        metrics_data = {"metrics": [], "runs": {}}
    
    # Append new metric
    metrics_data["metrics"].append(metric_entry)
    
    # Update run-specific metrics
    run_id = run_id or "default"
    if run_id not in metrics_data["runs"]:
        metrics_data["runs"][run_id] = {}
    metrics_data["runs"][run_id][name] = {
        "value": value,
        "timestamp": timestamp
    }
    
    # Write back to file
    with open(_metrics_file_path, 'w') as f:
        json.dump(metrics_data, f, indent=2)
    
    # Log to file as well
    logger = get_logger()
    logger.info(f"Metric logged: {name} = {value}")

def flush_metrics() -> None:
    """
    Flush all accumulated metrics to the JSON file.
    This ensures all metrics are persisted even if the program exits unexpectedly.
    """
    global _metrics, _metrics_file_path
    
    if _metrics_file_path is None:
        return
    
    if not _metrics:
        return
    
    try:
        with open(_metrics_file_path, 'r') as f:
            metrics_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        metrics_data = {"metrics": [], "runs": {}}
    
    # Add current session metrics
    timestamp = datetime.now().isoformat()
    for name, value in _metrics.items():
        metric_entry = {
            "name": name,
            "value": value,
            "timestamp": timestamp,
            "run_id": "default"
        }
        metrics_data["metrics"].append(metric_entry)
    
    # Write back
    with open(_metrics_file_path, 'w') as f:
        json.dump(metrics_data, f, indent=2)
    
    _metrics.clear()

def get_metrics() -> Dict[str, Any]:
    """
    Get all accumulated metrics for the current session.
    
    Returns:
        Dictionary of metric name -> value
    """
    return _metrics.copy()

def log_execution_summary(
    task_id: str,
    success: bool,
    duration_seconds: float,
    metrics: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an execution summary for a task run.
    
    Args:
        task_id: Task identifier
        success: Whether the task completed successfully
        duration_seconds: Execution duration in seconds
        metrics: Optional dictionary of metrics to record
    """
    logger = get_logger()
    
    summary = {
        "task_id": task_id,
        "success": success,
        "duration_seconds": duration_seconds,
        "timestamp": datetime.now().isoformat()
    }
    
    if metrics:
        summary["metrics"] = metrics
        for name, value in metrics.items():
            log_metric(name, value, run_id=task_id)
    
    status = "SUCCESS" if success else "FAILURE"
    logger.info(f"Task {task_id} {status} in {duration_seconds:.2f}s")
    
    # Log summary to file
    log_file = os.path.join(
        get_config()["paths"]["artifacts"], 
        "logs", 
        "execution_summary.json"
    )
    
    try:
        with open(log_file, 'r') as f:
            summaries = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        summaries = {"summaries": []}
    
    summaries["summaries"].append(summary)
    
    with open(log_file, 'w') as f:
        json.dump(summaries, f, indent=2)

def main():
    """
    Main entry point for testing logging utilities.
    """
    logger = setup_logging()
    
    logger.info("Testing logging utilities")
    
    # Test metric logging
    log_metric("test_metric_1", 42.5)
    log_metric("test_metric_2", {"key": "value"})
    
    # Test execution summary
    log_execution_summary(
        task_id="T009_TEST",
        success=True,
        duration_seconds=1.5,
        metrics={"accuracy": 0.95, "loss": 0.05}
    )
    
    # Flush metrics
    flush_metrics()
    
    logger.info("Logging test completed")

if __name__ == "__main__":
    main()
