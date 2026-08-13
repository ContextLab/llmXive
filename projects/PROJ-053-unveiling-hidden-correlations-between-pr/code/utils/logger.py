import logging
import time
import json
from contextlib import contextmanager
from typing import Optional
from pathlib import Path
from config import get_logger, ensure_directories, get_logs_dir, get_results_dir

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Setup logging configuration."""
    ensure_directories()
    
    logger = logging.getLogger("pipeline")
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler if specified
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger

@contextmanager
def log_execution_time(operation_name: str = "Operation"):
    """Context manager to log execution time of a block."""
    start_time = time.time()
    logger = logging.getLogger("pipeline")
    logger.info(f"Starting {operation_name}...")
    try:
        yield
    finally:
        end_time = time.time()
        elapsed_seconds = end_time - start_time
        logger.info(f"Completed {operation_name} in {elapsed_seconds:.2f} seconds.")
        return elapsed_seconds

def log_error_and_raise(exception: Exception, message: str = "An error occurred") -> None:
    """Log an error message and raise the exception."""
    logger = logging.getLogger("pipeline")
    logger.error(f"{message}: {str(exception)}")
    raise exception

def get_log_file_path() -> Path:
    """Get the path for the main log file."""
    return get_logs_dir() / "pipeline.log"

def save_runtime_metrics(total_runtime_seconds: float, time_limit: int) -> None:
    """Save runtime metrics to results/metrics.json."""
    ensure_directories()
    results_dir = get_results_dir()
    metrics_path = results_dir / "metrics.json"
    
    # Load existing metrics if present
    metrics = {}
    if metrics_path.exists():
        try:
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
        except (json.JSONDecodeError, IOError):
            metrics = {}
    
    # Update metrics
    metrics['total_runtime_seconds'] = total_runtime_seconds
    metrics['time_limit_seconds'] = time_limit
    metrics['runtime_status'] = 'PASS' if total_runtime_seconds < time_limit else 'FAIL'
    
    # Save updated metrics
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger = logging.getLogger("pipeline")
    status_msg = f"Runtime: {total_runtime_seconds:.2f}s / {time_limit}s ({metrics['runtime_status']})"
    if metrics['runtime_status'] == 'FAIL':
        logger.critical(f"Runtime exceeds 6-hour CI limit. {status_msg}")
    else:
        logger.info(f"PASS: Runtime within 6-hour limit. {status_msg}")
