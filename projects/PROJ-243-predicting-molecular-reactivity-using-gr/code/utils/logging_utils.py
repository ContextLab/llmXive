"""
Logging utilities for the llmXive project.

Provides structured logging to files and metrics tracking to a JSON file.
"""
import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import get_config, ensure_directories

_logger: Optional[logging.Logger] = None
_metrics: List[Dict[str, Any]] = []
_metrics_file_path: Optional[str] = None

def setup_logging(log_level: int = logging.INFO, run_id: Optional[str] = None) -> logging.Logger:
    """
    Configure the root logger and project-specific logger.
    
    Creates handlers for console and file output.
    File output is structured with timestamps and levels.
    
    Args:
        log_level: The logging level (e.g., logging.INFO).
        run_id: Optional unique identifier for the run to include in log filenames.
    
    Returns:
        The configured project logger instance.
    """
    global _logger, _metrics_file_path
    
    config = get_config()
    ensure_directories()
    
    # Determine log directory
    log_dir = os.path.join(config["paths"]["artifacts"], "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_suffix = f"_{run_id}" if run_id else ""
    log_filename = f"run_{timestamp}{run_suffix}.log"
    log_file_path = os.path.join(log_dir, log_filename)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # File Handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(log_level)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)
    
    # Project Logger
    _logger = logging.getLogger("llmXive")
    _logger.setLevel(log_level)
    
    # Metrics file path
    _metrics_file_path = os.path.join(config["paths"]["artifacts"], "metrics.json")
    
    return _logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Optional name for the logger (e.g., 'module.submodule').
    
    Returns:
        A logger instance.
    """
    if _logger is None:
        setup_logging()
    if name:
        return _logger.getChild(name)
    return _logger

def log_metric(metric_name: str, value: Any, step: Optional[int] = None, tags: Optional[Dict[str, str]] = None) -> None:
    """
    Log a metric to the metrics file and in-memory list.
    
    Args:
        metric_name: Name of the metric.
        value: Value of the metric.
        step: Optional step number (e.g., epoch).
        tags: Optional dictionary of tags (e.g., {'split': 'train'}).
    """
    if _metrics_file_path is None:
        setup_logging()
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "metric": metric_name,
        "value": value,
        "step": step,
        "tags": tags or {}
    }
    
    _metrics.append(entry)
    
    # Write to file immediately to ensure durability
    try:
        with open(_metrics_file_path, 'w') as f:
            json.dump(_metrics, f, indent=2)
    except IOError as e:
        get_logger().error(f"Failed to write metrics to file: {e}")

def flush_metrics() -> None:
    """
    Ensure all metrics are written to disk.
    """
    if _metrics_file_path and _metrics:
        try:
            with open(_metrics_file_path, 'w') as f:
                json.dump(_metrics, f, indent=2)
        except IOError as e:
            get_logger().error(f"Failed to flush metrics: {e}")

def get_metrics() -> List[Dict[str, Any]]:
    """
    Get the in-memory list of metrics.
    
    Returns:
        List of metric dictionaries.
    """
    return _metrics.copy()

def log_execution_summary(summary: Dict[str, Any]) -> None:
    """
    Log a summary of the execution at the end of a script.
    
    Args:
        summary: Dictionary containing summary data (e.g., {'status': 'success', 'duration': 120}).
    """
    logger = get_logger()
    logger.info("Execution Summary: %s", json.dumps(summary))
    log_metric("execution_summary", summary, tags={"type": "summary"})

def main():
    """
    Main function for testing the logging utility.
    """
    logger = setup_logging()
    logger.info("Logging system initialized successfully.")
    log_metric("test_metric", 42.0)
    flush_metrics()
    logger.info("Test metric logged and flushed.")
    print("Logging test completed. Check artifacts/logs/ and artifacts/metrics.json")

if __name__ == "__main__":
    main()
