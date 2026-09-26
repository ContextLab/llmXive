"""
Base logging infrastructure for pipeline tracking.

Provides centralized logging configuration, logger instances, and
utility functions for tracking pipeline execution, metrics, and errors.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from utils.config import get_project_root, get_output_path


# Global logger instance cache
_loggers: Dict[str, logging.Logger] = {}
_log_file_path: Optional[Path] = None


def _ensure_log_directory() -> Path:
    """Ensure the log directory exists."""
    log_dir = get_output_path() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def _get_log_file_path() -> Path:
    """Get or create the main pipeline log file path."""
    global _log_file_path
    if _log_file_path is None:
        log_dir = _ensure_log_directory()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        _log_file_path = log_dir / f"pipeline_{timestamp}.log"
    return _log_file_path


def get_pipeline_logger(name: str = "pipeline") -> logging.Logger:
    """
    Get a configured logger instance for pipeline tracking.

    Args:
        name: Logger name, typically "pipeline" or a module-specific name.

    Returns:
        A configured logging.Logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        _loggers[name] = logger
        return logger

    # Create file handler
    log_file = _get_log_file_path()
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _loggers[name] = logger
    return logger


def get_log_file_path() -> Path:
    """
    Get the path to the current pipeline log file.

    Returns:
        Path to the log file.
    """
    return _get_log_file_path()


def log_pipeline_start(pipeline_name: str, config: Optional[Dict[str, Any]] = None) -> None:
    """
    Log the start of a pipeline execution.

    Args:
        pipeline_name: Name of the pipeline being executed.
        config: Optional configuration dictionary to log.
    """
    logger = get_pipeline_logger()
    logger.info("=" * 80)
    logger.info(f"PIPELINE START: {pipeline_name}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    if config:
        logger.info(f"Configuration: {config}")
    logger.info("=" * 80)


def log_pipeline_end(pipeline_name: str, success: bool, duration_seconds: Optional[float] = None) -> None:
    """
    Log the end of a pipeline execution.

    Args:
        pipeline_name: Name of the pipeline that finished.
        success: Whether the pipeline completed successfully.
        duration_seconds: Optional execution duration in seconds.
    """
    logger = get_pipeline_logger()
    status = "SUCCESS" if success else "FAILED"
    logger.info("=" * 80)
    logger.info(f"PIPELINE END: {pipeline_name} - {status}")
    if duration_seconds is not None:
        logger.info(f"Duration: {duration_seconds:.2f} seconds")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Log file: {_get_log_file_path()}")
    logger.info("=" * 80)


def log_error(error: Exception, context: Optional[str] = None) -> None:
    """
    Log an error with optional context.

    Args:
        error: The exception that occurred.
        context: Optional context string describing where the error occurred.
    """
    logger = get_pipeline_logger()
    error_msg = f"{type(error).__name__}: {str(error)}"
    if context:
        logger.error(f"[{context}] {error_msg}")
    else:
        logger.error(error_msg)
    logger.exception("Full traceback:")


def log_metric(metric_name: str, value: Any, stage: Optional[str] = None) -> None:
    """
    Log a pipeline metric.

    Args:
        metric_name: Name of the metric.
        value: Value of the metric.
        stage: Optional stage name where the metric was recorded.
    """
    logger = get_pipeline_logger()
    if stage:
        logger.info(f"METRIC [{stage}]: {metric_name} = {value}")
    else:
        logger.info(f"METRIC: {metric_name} = {value}")


def log_chunk_info(chunk_id: int, total_chunks: int, items_processed: int, stage: str) -> None:
    """
    Log information about chunk processing progress.

    Args:
        chunk_id: Current chunk identifier.
        total_chunks: Total number of chunks.
        items_processed: Number of items processed so far.
        stage: Name of the processing stage.
    """
    logger = get_pipeline_logger()
    progress = (chunk_id / total_chunks * 100) if total_chunks > 0 else 0
    logger.info(f"CHUNK [{stage}] {chunk_id}/{total_chunks} ({progress:.1f}%) - Items processed: {items_processed}")


def log_task_start(task_id: str, task_name: str) -> None:
    """
    Log the start of a specific task.

    Args:
        task_id: Task identifier (e.g., "T006").
        task_name: Human-readable task name.
    """
    logger = get_pipeline_logger()
    logger.info(f"TASK START: {task_id} - {task_name}")


def log_task_end(task_id: str, task_name: str, success: bool, duration_seconds: float) -> None:
    """
    Log the end of a specific task.

    Args:
        task_id: Task identifier.
        task_name: Human-readable task name.
        success: Whether the task completed successfully.
        duration_seconds: Execution duration in seconds.
    """
    logger = get_pipeline_logger()
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"TASK END: {task_id} - {task_name} - {status} ({duration_seconds:.2f}s)")


def log_data_file_created(filepath: Path, size_bytes: int, record_count: Optional[int] = None) -> None:
    """
    Log the creation of a data file.

    Args:
        filepath: Path to the created file.
        size_bytes: Size of the file in bytes.
        record_count: Optional number of records in the file.
    """
    logger = get_pipeline_logger()
    size_mb = size_bytes / (1024 * 1024)
    msg = f"DATA FILE CREATED: {filepath} ({size_mb:.2f} MB)"
    if record_count is not None:
        msg += f" - {record_count} records"
    logger.info(msg)
