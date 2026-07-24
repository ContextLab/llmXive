"""
Performance Optimization Module for Neuro-Symbolic Pipeline.

This package contains utilities to ensure the pipeline operates within
the 7GB RAM constraint by implementing streaming data processing,
memory monitoring, and batch operations.
"""
from .memory_monitor import (
    MemoryMonitor,
    get_current_memory_mb,
    check_memory_limit,
    force_gc,
    stream_csv_batch,
    MemoryExceededError
)

from .batch_processor import (
    process_simulation_logs_batch,
    merge_datasets_streaming
)

__all__ = [
    'MemoryMonitor',
    'get_current_memory_mb',
    'check_memory_limit',
    'force_gc',
    'stream_csv_batch',
    'MemoryExceededError',
    'process_simulation_logs_batch',
    'merge_datasets_streaming'
]
