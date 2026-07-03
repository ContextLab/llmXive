"""
Logging utilities for memory usage tracking and structured logging.
"""
import logging
import sys
from typing import Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    psutil = None


def get_process_memory_mb() -> float:
    """
    Retrieves the current RSS (Resident Set Size) memory usage of the current process in MB.
    """
    if not HAS_PSUTIL:
        return 0.0
    process = psutil.Process()
    return process.memory_info().rss / (1024 * 1024)


def setup_memory_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Configures a logger that includes memory usage in its output format.
    If log_file is provided, also writes to that file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers to ensure clean state
    logger.handlers.clear()

    # Formatter that includes memory usage
    class MemoryFormatter(logging.Formatter):
        def format(self, record):
            if HAS_PSUTIL:
                record.memory_mb = f"{get_process_memory_mb():.2f}"
            else:
                record.memory_mb = "N/A"
            return super().format(record)

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(MemoryFormatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | [Mem: %(memory_mb)s MB] | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(ch)

    # File Handler (optional)
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(MemoryFormatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | [Mem: %(memory_mb)s MB] | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(fh)

    return logger


def log_memory_snapshot(logger: logging.Logger, message: str = "Memory Snapshot") -> float:
    """
    Logs the current memory usage with a custom message.
    Returns the memory usage in MB.
    """
    mem_mb = get_process_memory_mb()
    if HAS_PSUTIL:
        logger.info(f"{message}: {mem_mb:.2f} MB")
    else:
        logger.warning(f"{message}: psutil not installed, cannot report memory.")
    return mem_mb
