import os
import sys
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import get_config, ensure_directories

# Global state for metrics accumulation
_metrics_buffer: List[Dict[str, Any]] = []
_metrics_file_path: Optional[str] = None
_logger_instance: Optional[logging.Logger] = None

def setup_logging(log_file_path: str, level: int = logging.INFO) -> logging.Logger:
    """
    Configure the root logger and a project-specific logger.
    Sets up:
    1. File handler for structured logs (JSON-like format or standard text with timestamps).
    2. Console handler for immediate feedback.
    3. Metrics file handler for appending metrics to artifacts/metrics.json.

    Args:
        log_file_path: Path to the log file (e.g., 'artifacts/logs/run_20231027.log').
        level: Logging level.

    Returns:
        Configured logger instance.
    """
    global _metrics_file_path

    # Ensure directory exists
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    # Get or create logger
    logger = logging.getLogger('llmXive')
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates on re-runs in same process
    logger.handlers.clear()

    # Formatter for standard logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler for logs
    fh = logging.FileHandler(log_file_path, mode='a')
    fh.setLevel(level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Setup metrics file path
    _metrics_file_path = os.path.join(
        os.path.dirname(log_file_path), 
        os.pardir, 
        'metrics.json'
    )
    # Normalize path (resolve ..)
    _metrics_file_path = os.path.normpath(_metrics_file_path)
    
    # Ensure metrics directory exists
    os.makedirs(os.path.dirname(_metrics_file_path), exist_ok=True)

    # Initialize metrics file if it doesn't exist
    if not os.path.exists(_metrics_file_path):
        with open(_metrics_file_path, 'w') as f:
            json.dump({"metrics": []}, f)

    _logger_instance = logger
    logger.info(f"Logging initialized. Logs: {log_file_path}, Metrics: {_metrics_file_path}")
    return logger

def get_logger() -> logging.Logger:
    """Get the configured logger instance."""
    if _logger_instance is None:
        raise RuntimeError("Logging not initialized. Call setup_logging first.")
    return _logger_instance

def log_metric(metric_name: str, value: Any, tags: Optional[Dict[str, str]] = None) -> None:
    """
    Append a metric to the in-memory buffer and flush to disk.
    This ensures real-time persistence of metrics to artifacts/metrics.json.

    Args:
        metric_name: Name of the metric (e.g., 'loss', 'accuracy').
        value: Value of the metric.
        tags: Optional dictionary of metadata (e.g., {'epoch': 5, 'model': 'spectral'}).
    """
    global _metrics_buffer
    
    if _metrics_file_path is None:
        raise RuntimeError("Metrics file path not set. Call setup_logging first.")

    entry = {
        "timestamp": datetime.now().isoformat(),
        "metric": metric_name,
        "value": value,
        "tags": tags or {}
    }
    
    _metrics_buffer.append(entry)
    flush_metrics()

def get_metrics() -> List[Dict[str, Any]]:
    """Return the current buffer of metrics."""
    return _metrics_buffer.copy()

def flush_metrics() -> None:
    """
    Write the current metrics buffer to the metrics.json file.
    Reads the existing file, appends new entries, and writes back.
    """
    if _metrics_file_path is None or not _metrics_buffer:
        return

    try:
        # Read existing metrics
        existing_data = {"metrics": []}
        if os.path.exists(_metrics_file_path):
            with open(_metrics_file_path, 'r') as f:
                try:
                    existing_data = json.load(f)
                    if "metrics" not in existing_data:
                        existing_data["metrics"] = []
                except json.JSONDecodeError:
                    # If file is corrupted, start fresh but log warning
                    logging.getLogger('llmXive').warning(f"Corrupted metrics file at {_metrics_file_path}, resetting.")
        
        # Append new metrics
        existing_data["metrics"].extend(_metrics_buffer)
        
        # Write back
        with open(_metrics_file_path, 'w') as f:
            json.dump(existing_data, f, indent=2)
        
        # Clear buffer
        _metrics_buffer.clear()
    except Exception as e:
        logging.getLogger('llmXive').error(f"Failed to flush metrics to {_metrics_file_path}: {e}")

def log_execution_summary(summary_data: Dict[str, Any]) -> None:
    """
    Log a structured execution summary to the log file and metrics.
    
    Args:
        summary_data: Dictionary containing execution details (e.g., duration, status, counts).
    """
    logger = get_logger()
    logger.info(f"Execution Summary: {json.dumps(summary_data)}")
    log_metric("execution_summary", summary_data, tags={"type": "summary"})

def main():
    """
    Main entry point for testing the logging setup directly.
    Writes a sample log and metric to verify functionality.
    """
    config = get_config()
    ensure_directories(config)
    
    # Setup logging to a specific test file
    log_path = os.path.join(config['paths']['artifacts'], 'logs', 'test_run.log')
    logger = setup_logging(log_path)
    
    logger.info("Test log message 1")
    logger.warning("Test warning message")
    
    # Test metric logging
    log_metric("test_metric", 0.95, tags={"test": "true", "run_id": "T009-verify"})
    log_metric("test_metric", 0.96, tags={"test": "true", "run_id": "T009-verify"})
    
    # Force flush
    flush_metrics()
    
    logger.info("Logging test completed successfully.")
    
    # Verify files exist
    assert os.path.exists(log_path), f"Log file missing: {log_path}"
    metrics_path = os.path.join(config['paths']['artifacts'], 'metrics.json')
    assert os.path.exists(metrics_path), f"Metrics file missing: {metrics_path}"
    
    print(f"Verified: {log_path}")
    print(f"Verified: {metrics_path}")

if __name__ == "__main__":
    main()
