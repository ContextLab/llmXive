"""
Base logging infrastructure for the llmXive automated science pipeline.

Provides centralized logging configuration, pipeline tracking, and task
lifecycle logging to satisfy FR-002 (pipeline tracking) and support
reproducibility and debugging.

Exports:
    get_pipeline_logger: Returns a configured logger instance for the pipeline.
    get_log_file_path: Returns the absolute path to the current log file.
    log_pipeline_start: Logs the start of the entire pipeline run.
    log_pipeline_end: Logs the completion of the entire pipeline run.
    log_error: Logs an error with context and traceback.
    log_metric: Logs a quantitative metric (e.g., processing time, memory).
    log_chunk_info: Logs information about processed data chunks.
    log_task_start: Logs the beginning of a specific task.
    log_task_end: Logs the completion of a specific task.
    log_data_file_created: Logs when a new data artifact is written.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import traceback

from utils.config import get_project_root, get_logs_path

# Global logger instance cache to ensure consistent configuration
_logger_instance: Optional[logging.Logger] = None
_log_file_path: Optional[Path] = None


def _configure_logger() -> logging.Logger:
    """
    Configures and returns the main pipeline logger.
    
    Sets up:
        - File handler writing to data/logs/pipeline.log
        - Stream handler writing to stdout
        - Log format including timestamp, level, module, and message
        - Level set to DEBUG for full pipeline tracking
    """
    global _logger_instance, _log_file_path
    
    if _logger_instance is not None:
        return _logger_instance
    
    root_path = get_project_root()
    logs_dir = get_logs_path()
    
    # Ensure logs directory exists
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log file path with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"pipeline_{timestamp}.log"
    _log_file_path = logs_dir / log_filename
    
    # Create logger
    logger = logging.getLogger("llmXive_pipeline")
    logger.setLevel(logging.DEBUG)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        logger.handlers.clear()
    
    # Formatter with ISO timestamp and context
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # File handler
    fh = logging.FileHandler(_log_file_path, mode='w', encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Stream handler (stdout)
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    
    _logger_instance = logger
    return logger


def get_pipeline_logger() -> logging.Logger:
    """
    Returns the configured pipeline logger instance.
    
    Returns:
        logging.Logger: The configured logger for pipeline tracking.
    """
    return _configure_logger()


def get_log_file_path() -> Path:
    """
    Returns the absolute path to the current log file.
    
    Returns:
        Path: Path to the active log file.
    """
    if _log_file_path is None:
        _configure_logger()
    return _log_file_path


def log_pipeline_start(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Logs the start of the entire pipeline execution.
    
    Args:
        config: Optional dictionary of configuration parameters to log.
    """
    logger = get_pipeline_logger()
    logger.info("=" * 80)
    logger.info("PIPELINE EXECUTION STARTED")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    if config:
        logger.info(f"Configuration: {config}")
    logger.info("=" * 80)


def log_pipeline_end(status: str = "SUCCESS", error: Optional[str] = None) -> None:
    """
    Logs the completion of the entire pipeline execution.
    
    Args:
        status: Final status ("SUCCESS", "FAILED", "PARTIAL").
        error: Optional error message if status is FAILED.
    """
    logger = get_pipeline_logger()
    logger.info("=" * 80)
    logger.info(f"PIPELINE EXECUTION ENDED: {status}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    if error:
        logger.error(f"Error details: {error}")
    logger.info("=" * 80)


def log_error(task: str, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Logs an error with full traceback and optional context.
    
    Args:
        task: Name of the task where the error occurred.
        error: The exception instance.
        context: Optional dictionary of contextual variables.
    """
    logger = get_pipeline_logger()
    error_msg = f"ERROR in task '{task}': {str(error)}"
    logger.error(error_msg)
    logger.error(f"Traceback:\n{traceback.format_exc()}")
    if context:
        logger.error(f"Context: {context}")


def log_metric(metric_name: str, value: Any, unit: Optional[str] = None, task: Optional[str] = None) -> None:
    """
    Logs a quantitative metric (e.g., processing time, memory usage).
    
    Args:
        metric_name: Name of the metric.
        value: Numeric value of the metric.
        unit: Optional unit of measurement (e.g., "seconds", "MB").
        task: Optional task name for context.
    """
    logger = get_pipeline_logger()
    unit_str = f" [{unit}]" if unit else ""
    msg = f"METRIC: {metric_name} = {value}{unit_str}"
    if task:
        msg += f" (Task: {task})"
    logger.info(msg)


def log_chunk_info(chunk_id: int, total_chunks: int, records_processed: int, elapsed_seconds: float) -> None:
    """
    Logs information about a processed data chunk.
    
    Args:
        chunk_id: Current chunk index (1-based).
        total_chunks: Total number of chunks.
        records_processed: Number of records in this chunk.
        elapsed_seconds: Time taken to process this chunk.
    """
    logger = get_pipeline_logger()
    logger.info(
        f"CHUNK [{chunk_id}/{total_chunks}] | "
        f"Records: {records_processed} | "
        f"Elapsed: {elapsed_seconds:.2f}s"
    )


def log_task_start(task_id: str, description: Optional[str] = None) -> None:
    """
    Logs the beginning of a specific task.
    
    Args:
        task_id: Unique identifier for the task (e.g., "T006").
        description: Optional description of the task.
    """
    logger = get_pipeline_logger()
    msg = f"TASK START: {task_id}"
    if description:
        msg += f" - {description}"
    logger.info(msg)


def log_task_end(task_id: str, status: str = "COMPLETED", output_files: Optional[list] = None) -> None:
    """
    Logs the completion of a specific task.
    
    Args:
        task_id: Unique identifier for the task.
        status: Task status ("COMPLETED", "SKIPPED", "FAILED").
        output_files: Optional list of output file paths generated by the task.
    """
    logger = get_pipeline_logger()
    msg = f"TASK END: {task_id} -> {status}"
    if output_files:
        msg += f" | Outputs: {', '.join(str(f) for f in output_files)}"
    logger.info(msg)


def log_data_file_created(file_path: str, file_size_mb: Optional[float] = None, record_count: Optional[int] = None) -> None:
    """
    Logs when a new data artifact is written to disk.
    
    Args:
        file_path: Path to the created file.
        file_size_mb: Optional file size in megabytes.
        record_count: Optional number of records in the file.
    """
    logger = get_pipeline_logger()
    msg = f"DATA CREATED: {file_path}"
    if file_size_mb is not None:
        msg += f" | Size: {file_size_mb:.2f} MB"
    if record_count is not None:
        msg += f" | Records: {record_count}"
    logger.info(msg)
