"""
Memory-efficient logging infrastructure for the Prime Gap analysis pipeline.

This module provides:
- Chunked processing logs (batch-wise progress without holding state in memory).
- OOM (Out-Of-Memory) warning detection and handling.
- Structured log output suitable for large-scale data ingestion (primes up to 10^10).

It avoids storing large lists of logs in memory by flushing to disk immediately
and using a file-based handler with rotation.
"""

import logging
import os
import sys
import resource
from pathlib import Path
from typing import Optional, Dict, Any

# Constants for logging configuration
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "pipeline.log"
MAX_LOG_SIZE_MB = 10
BACKUP_COUNT = 5

# Memory threshold for warnings (7GB as per project constraints)
MEMORY_WARNING_THRESHOLD_BYTES = 7 * 1024 ** 3  # 7 GB
MEMORY_CRITICAL_THRESHOLD_BYTES = 7.5 * 1024 ** 3  # 7.5 GB

_logger: Optional[logging.Logger] = None


def _get_memory_usage_mb() -> float:
    """
    Returns current process memory usage in MB using resource module (Unix).
    Falls back to 0.0 on non-Unix systems (Windows) where resource.getrusage
    might not return RSS in the same way, though typically works on modern Windows.
    """
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux/macOS, but bytes on some Windows versions.
        # Standard Linux: ru_maxrss is in KB.
        # To be safe, we check platform or assume standard behavior for this pipeline.
        import platform
        if platform.system() == "Windows":
            # On Windows, ru_maxrss is in bytes
            return usage.ru_maxrss / (1024 * 1024)
        else:
            # On Linux/macOS, ru_maxrss is in KB
            return usage.ru_maxrss / 1024.0
    except Exception:
        # Fallback if resource module is unavailable
        return 0.0


def _check_memory_and_log(log_obj: logging.Logger, message_prefix: str = "Memory Check") -> None:
    """
    Checks current memory usage and logs a warning or critical error if thresholds are exceeded.
    """
    current_mb = _get_memory_usage_mb()
    current_bytes = current_mb * 1024 * 1024

    if current_bytes >= MEMORY_CRITICAL_THRESHOLD_BYTES:
        log_obj.critical(
            f"{message_prefix}: CRITICAL OOM RISK DETECTED. "
            f"Current Memory: {current_mb:.2f} MB (Threshold: {MEMORY_CRITICAL_THRESHOLD_BYTES / (1024**3):.2f} GB). "
            f"Pipeline may crash soon. Consider reducing chunk size."
        )
    elif current_bytes >= MEMORY_WARNING_THRESHOLD_BYTES:
        log_obj.warning(
            f"{message_prefix}: HIGH MEMORY USAGE. "
            f"Current Memory: {current_mb:.2f} MB (Threshold: {MEMORY_WARNING_THRESHOLD_BYTES / (1024**3):.2f} GB). "
            f"Approaching OOM limits."
        )


def get_logger(name: str = "prime_gap_pipeline") -> logging.Logger:
    """
    Retrieves or creates a configured logger instance.
    Ensures logs are written to disk with rotation to prevent disk space issues.
    """
    global _logger
    if _logger is not None and _logger.name == name:
        return _logger

    # Create logs directory if it doesn't exist
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_LOG_SIZE_MB * 1024 * 1024,
        backupCount=BACKUP_COUNT
    )
    file_handler.setLevel(logging.INFO)

    # Console handler for immediate feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _logger = logger
    return logger


def log_chunk_progress(
    logger: logging.Logger,
    chunk_id: int,
    total_chunks: int,
    items_processed: int,
    memory_check: bool = True
) -> None:
    """
    Logs progress for a specific chunk of processing.
    Optionally checks memory usage to warn about OOM risks.

    Args:
        logger: The logger instance to use.
        chunk_id: Current chunk index (1-based).
        total_chunks: Total number of chunks.
        items_processed: Number of items processed in this chunk.
        memory_check: Whether to check memory thresholds.
    """
    progress_pct = (chunk_id / total_chunks) * 100
    logger.info(
        f"Chunk Progress: [{chunk_id}/{total_chunks}] ({progress_pct:.1f}%) - "
        f"Items in this chunk: {items_processed}"
    )

    if memory_check:
        _check_memory_and_log(logger, f"Chunk {chunk_id}")


def log_oom_warning(logger: logging.Logger, context: str = "General") -> None:
    """
    Explicitly logs an OOM warning if the current memory usage is high.
    Useful for manual checks after heavy operations.
    """
    _check_memory_and_log(logger, f"OOM Check ({context})")


def log_error_with_memory_info(logger: logging.Logger, error: Exception, context: str = "") -> None:
    """
    Logs an error along with current memory usage to help diagnose OOM crashes.
    """
    current_mb = _get_memory_usage_mb()
    logger.error(
        f"Error in {context}: {error}. "
        f"Current Memory: {current_mb:.2f} MB. "
        f"Exception Type: {type(error).__name__}"
    )

    if current_mb > MEMORY_CRITICAL_THRESHOLD_BYTES / (1024 * 1024):
        logger.critical("Error likely caused by Out-Of-Memory conditions.")
