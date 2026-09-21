"""
Logging utilities for the llmXive science pipeline.

Provides structured logging to files and metrics tracking in JSON format.
"""
import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import get_config, ensure_directories

# Global state for metrics
_metrics_cache: Dict[str, Any] = {}
_metrics_file_path: Optional[str] = None

def setup_logging(
    logger_name: str = "pipeline",
    log_dir: Optional[str] = None,
    log_level: int = logging.INFO,
    console_output: bool = True
) -> logging.Logger:
    """
    Configure structured logging for the pipeline.
    
    Args:
        logger_name: Name of the logger to configure.
        log_dir: Directory to store log files. Defaults to config/artifacts/logs.
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG).
        console_output: Whether to also log to stdout.
        
    Returns:
        Configured logger instance.
    """
    config = get_config()
    
    if log_dir is None:
        log_dir = os.path.join(config.get("artifacts_dir", "artifacts"), "logs")
    
    ensure_directories([log_dir])
    
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Formatter for structured logs (JSON-like format for easier parsing)
    class StructuredFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_data)
    
    # File handler
    log_filename = f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file_path = os.path.join(log_dir, log_filename)
    
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(StructuredFormatter())
    logger.addHandler(file_handler)
    
    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        logger.addHandler(console_handler)
    
    return logger

def get_logger(name: str = "pipeline") -> logging.Logger:
    """
    Get a logger instance. If not configured, returns a basic logger.
    
    Args:
        name: Logger name.
        
    Returns:
        Logger instance.
    """
    return logging.getLogger(name)

def log_metric(
    metric_name: str,
    value: Any,
    metadata: Optional[Dict[str, Any]] = None,
    metrics_file: Optional[str] = None
) -> None:
    """
    Log a metric to the metrics JSON file.
    
    Args:
        metric_name: Name of the metric.
        value: Metric value (must be JSON serializable).
        metadata: Optional metadata dictionary.
        metrics_file: Path to metrics file. Defaults to config/artifacts/metrics.json.
    """
    config = get_config()
    
    if metrics_file is None:
        metrics_file = os.path.join(config.get("artifacts_dir", "artifacts"), "metrics.json")
    
    # Ensure directory exists
    ensure_directories([os.path.dirname(metrics_file)])
    
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "metric_name": metric_name,
        "value": value,
        "metadata": metadata or {}
    }
    
    # Load existing metrics if file exists
    metrics_data = []
    if os.path.exists(metrics_file):
        try:
            with open(metrics_file, 'r') as f:
                content = f.read().strip()
                if content:
                    metrics_data = json.loads(content)
                    if not isinstance(metrics_data, list):
                        metrics_data = [metrics_data]
        except (json.JSONDecodeError, IOError):
            metrics_data = []
    
    # Append new entry
    metrics_data.append(entry)
    
    # Write back
    with open(metrics_file, 'w') as f:
        json.dump(metrics_data, f, indent=2)

def get_metrics(metrics_file: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve all logged metrics from the metrics file.
    
    Args:
        metrics_file: Path to metrics file.
        
    Returns:
        List of metric entries.
    """
    config = get_config()
    
    if metrics_file is None:
        metrics_file = os.path.join(config.get("artifacts_dir", "artifacts"), "metrics.json")
    
    if not os.path.exists(metrics_file):
        return []
    
    try:
        with open(metrics_file, 'r') as f:
            content = f.read().strip()
            if not content:
                return []
            data = json.loads(content)
            return data if isinstance(data, list) else [data]
    except (json.JSONDecodeError, IOError):
        return []

def flush_metrics(metrics_file: Optional[str] = None) -> None:
    """
    Flush metrics cache to disk (if using in-memory caching).
    
    Currently, metrics are written immediately, so this is a no-op.
    Reserved for future optimization.
    """
    pass

def log_execution_summary(
    task_id: str,
    status: str,
    duration_seconds: float,
    metrics: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    log_dir: Optional[str] = None
) -> None:
    """
    Log an execution summary for a task.
    
    Args:
        task_id: Identifier for the task.
        status: Execution status ('success', 'failed', 'skipped').
        duration_seconds: Execution duration in seconds.
        metrics: Optional dictionary of metrics.
        error_message: Error message if status is 'failed'.
        log_dir: Directory for log files.
    """
    config = get_config()
    
    if log_dir is None:
        log_dir = os.path.join(config.get("artifacts_dir", "artifacts"), "logs")
    
    ensure_directories([log_dir])
    
    logger = logging.getLogger("pipeline.execution")
    logger.setLevel(logging.INFO)
    
    # Ensure handler exists
    if not logger.handlers:
        log_filename = f"execution_summary_{datetime.now().strftime('%Y%m%d')}.log"
        log_file_path = os.path.join(log_dir, log_filename)
        
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)
    
    summary = {
        "task_id": task_id,
        "status": status,
        "duration_seconds": duration_seconds,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if metrics:
        summary["metrics"] = metrics
    
    if error_message:
        summary["error"] = error_message
    
    if status == "success":
        logger.info(f"Task {task_id} completed successfully.", extra={"summary": summary})
    elif status == "failed":
        logger.error(f"Task {task_id} failed: {error_message}", extra={"summary": summary})
    else:
        logger.warning(f"Task {task_id} was skipped.", extra={"summary": summary})
    
    # Also log to metrics file
    if metrics:
        for key, value in metrics.items():
            log_metric(
                f"{task_id}.{key}",
                value,
                metadata={"task_status": status, "duration": duration_seconds},
                metrics_file=os.path.join(config.get("artifacts_dir", "artifacts"), "metrics.json")
            )

def main():
    """
    Main function for testing the logging utilities.
    """
    logger = setup_logging()
    
    logger.info("Logging system initialized.")
    
    log_metric("test_metric", 42.5, metadata={"source": "test"})
    
    summary = {
        "test_metric": 42.5,
        "test_duration": 1.23
    }
    
    log_execution_summary(
        task_id="T009",
        status="success",
        duration_seconds=1.5,
        metrics=summary
    )
    
    metrics = get_metrics()
    logger.info(f"Retrieved {len(metrics)} metrics.")
    
    print("Logging utilities test completed successfully.")

if __name__ == "__main__":
    main()
