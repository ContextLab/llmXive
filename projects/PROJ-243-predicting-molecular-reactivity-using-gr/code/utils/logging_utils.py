"""
Logging utilities for the llmXive pipeline.

Provides structured logging to files and metrics tracking to JSON.
"""
import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import ensure_directories, get_config

# Global metrics store
_metrics: Dict[str, Any] = {}
_metrics_file: Optional[str] = None
_logger: Optional[logging.Logger] = None

def setup_logging(
    log_dir: str = "artifacts/logs",
    log_level: int = logging.INFO,
    run_id: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging infrastructure.
    
    Args:
        log_dir: Directory for log files.
        log_level: Logging level (e.g., logging.INFO).
        run_id: Optional run identifier for log file naming.
    
    Returns:
        Configured logger instance.
    """
    global _logger, _metrics_file
    
    # Ensure directories exist
    ensure_directories([log_dir, "artifacts/metrics"])
    
    # Generate run ID if not provided
    if run_id is None:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Log file paths
    log_file = os.path.join(log_dir, f"run_{run_id}.log")
    _metrics_file = "artifacts/metrics.json"
    
    # Create logger
    _logger = logging.getLogger("llmXive")
    _logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    _logger.handlers.clear()
    
    # File handler for detailed logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    _logger.addHandler(file_handler)
    
    # Console handler for critical errors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR)
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    _logger.addHandler(console_handler)
    
    # Also add a general console handler for INFO+
    info_console = logging.StreamHandler(sys.stdout)
    info_console.setLevel(logging.INFO)
    info_console.setFormatter(file_formatter)
    _logger.addHandler(info_console)
    
    _logger.info(f"Logging initialized. Run ID: {run_id}")
    _logger.info(f"Log file: {log_file}")
    _logger.info(f"Metrics file: {_metrics_file}")
    
    return _logger

def get_logger() -> Optional[logging.Logger]:
    """Get the configured logger instance."""
    return _logger

def log_metric(key: str, value: Any, step: Optional[int] = None) -> None:
    """
    Log a metric to the in-memory store and the metrics file.
    
    Args:
        key: Metric name.
        value: Metric value.
        step: Optional step/epoch number.
    """
    global _metrics
    
    if _metrics_file is None:
        # Fallback if logging not set up yet
        if not _logger:
            setup_logging()
        _logger.warning(f"Metrics logging not fully initialized. Storing {key} in memory.")
    
    timestamp = datetime.now().isoformat()
    metric_entry = {
        "key": key,
        "value": value,
        "timestamp": timestamp,
        "step": step
    }
    
    # Store in memory
    if key not in _metrics:
        _metrics[key] = []
    _metrics[key].append(metric_entry)
    
    # Write to file
    try:
        # Load existing metrics if file exists
        if os.path.exists(_metrics_file):
            with open(_metrics_file, 'r') as f:
                existing = json.load(f)
        else:
            existing = {}
        
        # Update
        if key not in existing:
            existing[key] = []
        existing[key].append(metric_entry)
        
        # Write back
        with open(_metrics_file, 'w') as f:
            json.dump(existing, f, indent=2)
            
    except Exception as e:
        if _logger:
            _logger.error(f"Failed to write metrics to file: {e}")
        else:
            print(f"Error writing metrics: {e}")

def get_metrics() -> Dict[str, List[Dict[str, Any]]]:
    """Get all logged metrics from memory."""
    return _metrics.copy()

def flush_metrics() -> None:
    """Force flush metrics to disk."""
    global _metrics, _metrics_file
    
    if _metrics_file and os.path.exists(_metrics_file):
        try:
            with open(_metrics_file, 'r') as f:
                data = json.load(f)
            with open(_metrics_file, 'w') as f:
                json.dump(data, f, indent=2)
            if _logger:
                _logger.info("Metrics flushed to disk.")
        except Exception as e:
            if _logger:
                _logger.error(f"Error flushing metrics: {e}")

def log_execution_summary(
    task_id: str,
    success: bool,
    duration_seconds: float,
    message: Optional[str] = None
) -> None:
    """
    Log a structured execution summary for a task.
    
    Args:
        task_id: The task identifier (e.g., 'T009').
        success: Whether the task completed successfully.
        duration_seconds: Execution duration.
        message: Optional summary message.
    """
    if not _logger:
        setup_logging()
    
    summary = {
        "task_id": task_id,
        "success": success,
        "duration_seconds": duration_seconds,
        "timestamp": datetime.now().isoformat(),
        "message": message
    }
    
    # Log to file
    level = logging.INFO if success else logging.ERROR
    _logger.log(level, f"EXECUTION_SUMMARY: {json.dumps(summary)}")
    
    # Also log as a metric
    log_metric(f"task_{task_id}_status", "success" if success else "failed")
    log_metric(f"task_{task_id}_duration", duration_seconds)

def main() -> None:
    """
    Main entry point for standalone testing of logging utilities.
    """
    logger = setup_logging()
    logger.info("Testing logging utilities...")
    
    # Test metric logging
    log_metric("test_metric", 42.5)
    log_metric("test_metric", 43.0, step=1)
    
    # Test execution summary
    log_execution_summary("TEST-TASK", True, 1.23, "Test completed successfully")
    
    # Flush and verify
    flush_metrics()
    
    logger.info("Logging utilities test completed.")

if __name__ == "__main__":
    main()
