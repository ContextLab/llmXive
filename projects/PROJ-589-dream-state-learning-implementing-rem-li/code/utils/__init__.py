"""
Utilities package for the Dream-State Learning pipeline.
"""
from .logger import get_logger, log_event, JsonFormatter
from .memory_monitor import MemoryMonitor, MemoryLimitExceeded, enforce_memory_limit
from .exceptions import DataIntegrityError, TimeLimitExceeded
from .perf_optimizer import (
    BatchingStrategy,
    OptimizedDataset,
    PrefetchDataLoader,
    optimize_memory_for_training,
    efficient_batch_training,
    get_optimization_report
)

__all__ = [
    'get_logger',
    'log_event',
    'JsonFormatter',
    'MemoryMonitor',
    'MemoryLimitExceeded',
    'enforce_memory_limit',
    'DataIntegrityError',
    'TimeLimitExceeded',
    'BatchingStrategy',
    'OptimizedDataset',
    'PrefetchDataLoader',
    'optimize_memory_for_training',
    'efficient_batch_training',
    'get_optimization_report'
]
