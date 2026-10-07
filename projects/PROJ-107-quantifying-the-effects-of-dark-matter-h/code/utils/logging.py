import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from utils.config import get_project_root, get_logs_path


def get_pipeline_logger(name: str = "pipeline") -> logging.Logger:
    """
    Creates and configures a pipeline logger with file and console handlers.
    
    Args:
        name: The name of the logger (default: "pipeline")
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers if they already exist
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Create logs directory if it doesn't exist
    logs_path = get_logs_path()
    logs_path.mkdir(parents=True, exist_ok=True)
    
    # File handler with timestamp
    log_file = logs_path / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Formatter with timestamp, level, and message
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_log_file_path(logger: logging.Logger) -> Optional[Path]:
    """
    Retrieves the log file path for a given logger.
    
    Args:
        logger: The logger instance.
    
    Returns:
        Path to the log file, or None if not found.
    """
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            return Path(handler.filename)
    return None


def log_pipeline_start(logger: logging.Logger, task_id: str, stage: str) -> None:
    """
    Logs the start of a pipeline stage.
    
    Args:
        logger: The logger instance.
        task_id: The task identifier.
        stage: The pipeline stage name.
    """
    logger.info(f"=== PIPELINE START: Task {task_id}, Stage: {stage} ===")
    logger.info(f"Started at: {datetime.now().isoformat()}")


def log_pipeline_end(logger: logging.Logger, task_id: str, status: str, duration: float) -> None:
    """
    Logs the end of a pipeline stage.
    
    Args:
        logger: The logger instance.
        task_id: The task identifier.
        status: The execution status (SUCCESS/FAILED).
        duration: Execution duration in seconds.
    """
    logger.info(f"=== PIPELINE END: Task {task_id} ===")
    logger.info(f"Status: {status}")
    logger.info(f"Duration: {duration:.2f} seconds")
    logger.info(f"Ended at: {datetime.now().isoformat()}")


def log_error(logger: logging.Logger, error: Exception, context: Optional[str] = None) -> None:
    """
    Logs an error with optional context.
    
    Args:
        logger: The logger instance.
        error: The exception that occurred.
        context: Optional context information.
    """
    error_msg = f"ERROR: {str(error)}"
    if context:
        error_msg += f" | Context: {context}"
    logger.error(error_msg, exc_info=True)


def log_metric(logger: logging.Logger, metric_name: str, value: Any, unit: Optional[str] = None) -> None:
    """
    Logs a metric value.
    
    Args:
        logger: The logger instance.
        metric_name: The name of the metric.
        value: The metric value.
        unit: Optional unit of measurement.
    """
    unit_str = f" ({unit})" if unit else ""
    logger.info(f"METRIC: {metric_name}{unit_str} = {value}")


def log_chunk_info(logger: logging.Logger, chunk_id: int, total_chunks: int, 
                   rows_processed: int, elapsed_time: float) -> None:
    """
    Logs information about a data processing chunk.
    
    Args:
        logger: The logger instance.
        chunk_id: The chunk identifier.
        total_chunks: Total number of chunks.
        rows_processed: Number of rows processed in this chunk.
        elapsed_time: Time taken for this chunk in seconds.
    """
    logger.info(f"CHUNK: {chunk_id}/{total_chunks} | Rows: {rows_processed} | Time: {elapsed_time:.2f}s")


def log_task_start(logger: logging.Logger, task_name: str) -> None:
    """
    Logs the start of a specific task.
    
    Args:
        logger: The logger instance.
        task_name: The name of the task.
    """
    logger.info(f"TASK START: {task_name}")


def log_task_end(logger: logging.Logger, task_name: str, status: str) -> None:
    """
    Logs the end of a specific task.
    
    Args:
        logger: The logger instance.
        task_name: The name of the task.
        status: The task status (SUCCESS/FAILED).
    """
    logger.info(f"TASK END: {task_name} | Status: {status}")


def log_data_file_created(logger: logging.Logger, file_path: Path, rows: int) -> None:
    """
    Logs the creation of a data file.
    
    Args:
        logger: The logger instance.
        file_path: Path to the created file.
        rows: Number of rows in the file.
    """
    logger.info(f"DATA FILE CREATED: {file_path.name} | Rows: {rows} | Path: {file_path}")
