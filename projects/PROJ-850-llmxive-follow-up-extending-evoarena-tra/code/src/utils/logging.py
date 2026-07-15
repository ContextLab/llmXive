"""
Structured logging utilities for the EvoMem-Conflict Filtering pipeline.

This module provides:
- get_logger: Returns a configured logger instance for the project.
- ExecutionTimer: Context manager to measure inference/retrieval time.
- log_metrics: Appends execution metrics (tokens, time, status) to a CSV log.
"""
import csv
import os
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List


# Constants
DEFAULT_LOG_DIR = Path("data/logs")
DEFAULT_LOG_FILE = "execution_metrics.csv"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _ensure_log_dir(log_dir: Optional[Path] = None) -> Path:
    """Ensure the log directory exists."""
    if log_dir is None:
        log_dir = DEFAULT_LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_logger(name: str = "evomem", log_dir: Optional[Path] = None) -> logging.Logger:
    """
    Returns a configured logger instance.
    
    Args:
        name: Logger name (e.g., "evomem.conflict_detector").
        log_dir: Optional directory to write logs. Defaults to data/logs.
        
    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    
    # Avoid adding duplicate handlers if called multiple times
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler (optional, for persistent logs)
        if log_dir is not None:
            log_path = _ensure_log_dir(log_dir) / f"{name}.log"
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(console_formatter)
            logger.addHandler(file_handler)
    
    return logger


class ExecutionTimer:
    """
    Context manager to measure execution time in seconds.
    
    Usage:
        with ExecutionTimer() as timer:
            # do work
        elapsed = timer.elapsed_seconds
    """
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.elapsed_seconds: float = 0.0
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        if self.start_time is not None:
            self.elapsed_seconds = self.end_time - self.start_time


def log_metrics(
    log_file: Optional[Path] = None,
    task_id: Optional[str] = None,
    agent_variant: Optional[str] = None,
    context_tokens: Optional[int] = None,
    inference_time: Optional[float] = None,
    success_status: bool = True,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Appends a row of execution metrics to a CSV log file.
    
    Args:
        log_file: Path to the CSV log file. Defaults to data/logs/execution_metrics.csv.
        task_id: Identifier for the task being executed.
        agent_variant: Name of the agent variant (e.g., 'EvoMem-All', 'EvoMem-Conflict').
        context_tokens: Number of tokens in the input context.
        inference_time: Time taken for inference in seconds.
        success_status: Boolean indicating if the task succeeded.
        error_message: Optional error message if success_status is False.
        metadata: Optional dictionary of additional key-value pairs to log.
        
    Returns:
        Path to the updated log file.
    """
    if log_file is None:
        log_file = _ensure_log_dir() / DEFAULT_LOG_FILE
    
    # Ensure file exists and has headers
    file_exists = log_file.exists()
    
    row = {
        "timestamp": datetime.now().strftime(DATE_FORMAT),
        "task_id": task_id or "unknown",
        "agent_variant": agent_variant or "unknown",
        "context_tokens": context_tokens if context_tokens is not None else -1,
        "inference_time": inference_time if inference_time is not None else -1.0,
        "success_status": success_status,
        "error_message": error_message or ""
    }
    
    # Add metadata fields
    if metadata:
        for key, value in metadata.items():
            row[key] = str(value) if not isinstance(value, str) else value
    
    # Define standard fields for header consistency
    standard_fields = ["timestamp", "task_id", "agent_variant", "context_tokens", 
                       "inference_time", "success_status", "error_message"]
    
    # Determine all fields (standard + any new metadata keys)
    all_fields = standard_fields
    if metadata:
        for key in metadata.keys():
            if key not in all_fields:
                all_fields.append(key)
    
    with open(log_file, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=all_fields)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(row)
    
    return log_file