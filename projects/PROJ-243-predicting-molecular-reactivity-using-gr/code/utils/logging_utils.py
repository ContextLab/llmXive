import os
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Optional, Dict, Any, List

# Global logger instance to be used across the project
_logger: Optional[logging.Logger] = None
_metrics_buffer: List[Dict[str, Any]] = []
_metrics_file_path: str = "artifacts/metrics.json"

def setup_logging(
    log_dir: str = "artifacts/logs",
    log_level: int = logging.INFO,
    metrics_file: str = "artifacts/metrics.json",
) -> logging.Logger:
    """
    Configure the global logging infrastructure.

    Creates:
    1. A file handler writing structured logs to `log_dir`.
    2. A JSON metrics file at `metrics_file`.
    3. A global logger instance with these handlers.

    Args:
        log_dir: Directory to store log files.
        log_level: Logging level (e.g., logging.INFO).
        metrics_file: Path to the JSON metrics file.

    Returns:
        The configured logger instance.
    """
    global _logger, _metrics_file_path
    _metrics_file_path = metrics_file

    # Ensure directories exist
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(os.path.dirname(metrics_file), exist_ok=True)

    # Initialize the global logger
    _logger = logging.getLogger("llmXive")
    _logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    if _logger.handlers:
        _logger.handlers.clear()

    # Create formatter for text logs
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler for general logs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"run_{timestamp}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)

    # Console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)

    # Initialize empty metrics file
    with open(_metrics_file_path, 'w') as f:
        json.dump([], f)

    _logger.info(f"Logging infrastructure initialized. Logs: {log_file}, Metrics: {_metrics_file_path}")
    return _logger

def get_logger() -> logging.Logger:
    """
    Retrieve the global logger instance.
    Raises RuntimeError if setup_logging has not been called.
    """
    if _logger is None:
        raise RuntimeError("Logger not initialized. Call setup_logging() first.")
    return _logger

def log_metric(metric_name: str, value: Any, step: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a metric to the global metrics buffer and immediately flush to disk.

    Args:
        metric_name: Name of the metric.
        value: The metric value (numeric or serializable).
        step: Optional step/epoch index.
        metadata: Optional dictionary of additional context.
    """
    global _metrics_buffer, _metrics_file_path
    if _logger is None:
        # Fallback if logger isn't set up yet, though ideally setup_logging is called first
        setup_logging()

    entry = {
        "timestamp": datetime.now().isoformat(),
        "metric": metric_name,
        "value": value,
        "step": step,
        "metadata": metadata or {}
    }

    _metrics_buffer.append(entry)
    flush_metrics()
    _logger.debug(f"Metric logged: {metric_name} = {value}")

def flush_metrics() -> None:
    """
    Write the current metrics buffer to the JSON file.
    This ensures metrics are persisted even if the script crashes.
    """
    global _metrics_buffer, _metrics_file_path
    try:
        with open(_metrics_file_path, 'r') as f:
            existing_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []

    existing_data.extend(_metrics_buffer)
    _metrics_buffer = []

    with open(_metrics_file_path, 'w') as f:
        json.dump(existing_data, f, indent=2)

def get_metrics() -> List[Dict[str, Any]]:
    """
    Read and return all metrics currently in the file.
    """
    global _metrics_file_path
    try:
        with open(_metrics_file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def log_execution_summary(summary_data: Dict[str, Any]) -> None:
    """
    Log a structured summary of a task execution (e.g., success/failure, duration).

    Args:
        summary_data: Dictionary containing summary details.
    """
    if _logger is None:
        setup_logging()

    _logger.info(f"Execution Summary: {json.dumps(summary_data)}")
    log_metric("execution_summary", summary_data, metadata={"type": "summary"})

def main():
    """
    Standalone test runner for the logging utility.
    """
    logger = setup_logging()
    logger.info("Testing logging infrastructure...")
    
    log_metric("test_metric", 0.95, step=1)
    log_metric("test_metric", 0.98, step=2)
    
    log_execution_summary({
        "status": "success",
        "task": "T008",
        "message": "Logging infrastructure verified."
    })

    metrics = get_metrics()
    logger.info(f"Retrieved {len(metrics)} metrics from file.")
    print(f"Metrics saved to {os.path.abspath('artifacts/metrics.json')}")

if __name__ == "__main__":
    main()
