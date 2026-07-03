"""
Base logging infrastructure for the llmXive pipeline.
Provides a centralized logger configuration and utility functions
for tracking pipeline execution, errors, and metrics.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Import path constants from existing config module
from utils.config import get_project_root, get_output_path

# Global logger instance
_logger: Optional[logging.Logger] = None
_log_file_path: Optional[Path] = None

# Log levels mapping
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

def get_pipeline_logger(
    name: str = "llmXive",
    level: str = "INFO",
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    Initialize and return the centralized pipeline logger.
    
    This function ensures a single logger instance is created with
    both file and console handlers. It configures the logger to
    write to a timestamped log file in the project's output directory.
    
    Args:
        name: Logger name (default: "llmXive")
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional custom log file path. If None, uses default pipeline.log
        console: Whether to log to console (default: True)
    
    Returns:
        Configured logging.Logger instance
    """
    global _logger, _log_file_path
    
    if _logger is not None:
        return _logger
    
    # Create logger
    _logger = logging.getLogger(name)
    _logger.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))
    
    # Prevent duplicate handlers if called multiple times
    if _logger.handlers:
        _logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))
        ch.setFormatter(formatter)
        _logger.addHandler(ch)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
    else:
        # Default log file: project_root/logs/pipeline_<timestamp>.log
        logs_dir = get_output_path() / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"pipeline_{timestamp}.log"
        log_path = logs_dir / log_filename
    
    _log_file_path = log_path
    fh = logging.FileHandler(log_path)
    fh.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))
    fh.setFormatter(formatter)
    _logger.addHandler(fh)
    
    _logger.info(f"Pipeline logger initialized. Log file: {log_path}")
    
    return _logger

def log_pipeline_start(task_id: str, config: Dict[str, Any]) -> None:
    """
    Log the start of a pipeline task with configuration details.
    
    Args:
        task_id: The identifier of the task being executed (e.g., "T006")
        config: Dictionary of configuration parameters to log
    """
    logger = get_pipeline_logger()
    logger.info(f"--- TASK START: {task_id} ---")
    logger.info(f"Config: {config}")
    logger.info(f"Working directory: {get_project_root()}")

def log_pipeline_end(task_id: str, status: str, duration_seconds: Optional[float] = None) -> None:
    """
    Log the completion of a pipeline task.
    
    Args:
        task_id: The identifier of the task
        status: Final status (e.g., "SUCCESS", "FAILED", "PARTIAL")
        duration_seconds: Optional execution duration in seconds
    """
    logger = get_pipeline_logger()
    msg = f"--- TASK END: {task_id} | Status: {status}"
    if duration_seconds is not None:
        msg += f" | Duration: {duration_seconds:.2f}s"
    logger.info(msg)

def log_error(task_id: str, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a pipeline error with context.
    
    Args:
        task_id: The identifier of the task
        error: The exception that occurred
        context: Optional dictionary of contextual information
    """
    logger = get_pipeline_logger()
    logger.error(f"--- ERROR in {task_id} ---")
    logger.error(f"Error type: {type(error).__name__}")
    logger.error(f"Error message: {str(error)}")
    if context:
        logger.error(f"Context: {context}")
    logger.error("--- END ERROR ---")

def log_metric(task_id: str, metric_name: str, value: float, unit: Optional[str] = None) -> None:
    """
    Log a numeric metric during pipeline execution.
    
    Args:
        task_id: The identifier of the task
        metric_name: Name of the metric (e.g., "haloes_processed", "p_value")
        value: The metric value
        unit: Optional unit string (e.g., "count", "seconds")
    """
    logger = get_pipeline_logger()
    unit_str = f" ({unit})" if unit else ""
    logger.info(f"[{task_id}] Metric: {metric_name} = {value}{unit_str}")

def get_log_file_path() -> Optional[Path]:
    """
    Get the path to the current pipeline log file.
    
    Returns:
        Path to the log file, or None if logger not initialized
    """
    return _log_file_path

# Initialize logger immediately on module import for immediate use
# Default level can be overridden via environment variable LOG_LEVEL
default_level = os.getenv("LOG_LEVEL", "INFO")
get_pipeline_logger(level=default_level)
