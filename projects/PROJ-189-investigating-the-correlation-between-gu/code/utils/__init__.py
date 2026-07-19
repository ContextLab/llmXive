"""
Utilities package for the Gut Microbiome project.
Exposes logging and monitoring tools.
"""
from .logging import (
    get_logger,
    setup_logging,
    get_memory_usage_mb,
    log_memory_usage,
    MemoryMonitor,
    monitor_memory,
    check_memory_limit,
    HAS_PSUTIL
)

__all__ = [
    "get_logger",
    "setup_logging",
    "get_memory_usage_mb",
    "log_memory_usage",
    "MemoryMonitor",
    "monitor_memory",
    "check_memory_limit",
    "HAS_PSUTIL"
]