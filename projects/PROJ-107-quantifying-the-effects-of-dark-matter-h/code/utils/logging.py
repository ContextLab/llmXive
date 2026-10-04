"""
Logging infrastructure for the llmXive automated science pipeline.
Provides centralized logger configuration, file handlers, and utility
functions for tracking pipeline execution, metrics, and errors.
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from utils.config import get_project_root, get_logs_path


# Global logger instance cache
_loggers: Dict[str, logging.Logger] = {}


def get_pipeline_logger(name: str = "pipeline") -> logging.Logger:
    """
    Retrieve or create a logger configured for the pipeline.
    
    Args:
        name: Logger name (e.g., "ingestion", "processing", "analysis")
    
    Returns:
        Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)

    # Create file handler
    log_dir = get_logs_path()
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"{name}_{timestamp}.log"
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    _loggers[name] = logger
    return logger


def get_log_file_path(logger_name: str = "pipeline") -> Path:
    """
    Get the path to the most recent log file for a logger.
    
    Args:
        logger_name: Logger name to find log file for
    
    Returns:
        Path to the log file
    """
    log_dir = get_logs_path()
    if not log_dir.exists():
        return log_dir / f"{logger_name}_no_logs_yet.log"
    
    # Find most recent log file for this logger
    log_files = sorted(log_dir.glob(f"{logger_name}_*.log"), reverse=True)
    if log_files:
        return log_files[0]
    return log_dir / f"{logger_name}_no_logs_yet.log"


def log_pipeline_start(pipeline_version: str = "1.0.0", stage: str = "full") -> None:
    """
    Log the start of a pipeline execution.
    
    Args:
        pipeline_version: Version of the pipeline
        stage: Current stage (e.g., "ingestion", "processing", "full")
    """
    logger = get_pipeline_logger()
    logger.info("=" * 80)
    logger.info("PIPELINE EXECUTION STARTED")
    logger.info(f"Version: {pipeline_version}")
    logger.info(f"Stage: {stage}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 80)


def log_pipeline_end(status: str = "SUCCESS", duration_seconds: Optional[float] = None) -> None:
    """
    Log the end of a pipeline execution.
    
    Args:
        status: Final status (SUCCESS, FAILED, PARTIAL)
        duration_seconds: Total execution time in seconds
    """
    logger = get_pipeline_logger()
    logger.info("=" * 80)
    logger.info("PIPELINE EXECUTION ENDED")
    logger.info(f"Status: {status}")
    if duration_seconds is not None:
        logger.info(f"Duration: {duration_seconds:.2f} seconds")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 80)


def log_error(error: Exception, context: str = "") -> None:
    """
    Log an error with full traceback.
    
    Args:
        error: Exception that occurred
        context: Additional context about where the error occurred
    """
    logger = get_pipeline_logger()
    logger.error(f"ERROR: {error}")
    if context:
        logger.error(f"Context: {context}")
    logger.exception("Full traceback:")


def log_metric(metric_name: str, value: Any, unit: str = "", tags: Optional[Dict[str, str]] = None) -> None:
    """
    Log a metric value.
    
    Args:
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement (optional)
        tags: Additional tags for the metric
    """
    logger = get_pipeline_logger()
    msg = f"METRIC: {metric_name} = {value}"
    if unit:
        msg += f" ({unit})"
    if tags:
        tag_str = ", ".join(f"{k}={v}" for k, v in tags.items())
        msg += f" | Tags: {tag_str}"
    logger.info(msg)


def log_chunk_info(chunk_index: int, total_chunks: int, rows_processed: int, elapsed_seconds: float) -> None:
    """
    Log progress information for chunked processing.
    
    Args:
        chunk_index: Current chunk index (0-based)
        total_chunks: Total number of chunks
        rows_processed: Number of rows processed so far
        elapsed_seconds: Time elapsed since start
    """
    logger = get_pipeline_logger()
    progress = ((chunk_index + 1) / total_chunks) * 100
    logger.info(
        f"CHUNK PROGRESS: [{chunk_index + 1}/{total_chunks}] "
        f"({progress:.1f}%) - Rows: {rows_processed:,} - Elapsed: {elapsed_seconds:.2f}s"
    )


def log_task_start(task_id: str, description: str) -> None:
    """
    Log the start of a specific task.
    
    Args:
        task_id: Task identifier (e.g., "T006")
        description: Brief description of the task
    """
    logger = get_pipeline_logger()
    logger.info(f"TASK START: {task_id} - {description}")


def log_task_end(task_id: str, status: str = "COMPLETED", output_files: Optional[list] = None) -> None:
    """
    Log the end of a specific task.
    
    Args:
        task_id: Task identifier
        status: Task status (COMPLETED, FAILED, SKIPPED)
        output_files: List of output files generated
    """
    logger = get_pipeline_logger()
    msg = f"TASK END: {task_id} - Status: {status}"
    if output_files:
        msg += f" | Outputs: {', '.join(output_files)}"
    logger.info(msg)


def log_data_file_created(file_path: str, row_count: int, file_size_mb: float) -> None:
    """
    Log the creation of a data file.
    
    Args:
        file_path: Path to the created file
        row_count: Number of rows in the file
        file_size_mb: File size in megabytes
    """
    logger = get_pipeline_logger()
    logger.info(
        f"DATA FILE CREATED: {file_path} | "
        f"Rows: {row_count:,} | Size: {file_size_mb:.2f} MB"
    )