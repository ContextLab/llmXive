import os
import time
import tracemalloc
import logging
from typing import Optional, Dict, Any, Callable, TypeVar, ContextManager
from contextlib import contextmanager

from logging_config import setup_logging

logger = setup_logging(__name__)

T = TypeVar("T")


class ProfileResult:
    """Container for profiling results."""

    def __init__(
        self,
        start_time: float,
        end_time: float,
        peak_memory_mb: float,
        duration_ms: float
    ) -> None:
        self.start_time = start_time
        self.end_time = end_time
        self.peak_memory_mb = peak_memory_mb
        self.duration_ms = duration_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "peak_memory_mb": self.peak_memory_mb,
            "duration_ms": self.duration_ms,
        }


def get_process_memory_mb() -> float:
    """Get current process memory usage in MB."""
    import psutil
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def get_peak_memory_mb() -> float:
    """Get peak memory usage in MB."""
    if not tracemalloc.is_tracing():
        return 0.0
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)


def start_profiling() -> None:
    """Start memory and time profiling."""
    if not tracemalloc.is_tracing():
        tracemalloc.start()
    logger.debug("Profiling started")


def stop_profiling() -> float:
    """Stop profiling and return peak memory in MB."""
    if tracemalloc.is_tracing():
        peak = get_peak_memory_mb()
        tracemalloc.stop()
        logger.debug(f"Profiling stopped. Peak memory: {peak:.2f} MB")
        return peak
    return 0.0


@contextmanager
def profile_block(label: str = "block") -> Any:
    """Context manager to profile a code block."""
    start = time.time()
    start_mem = get_process_memory_mb()
    if not tracemalloc.is_tracing():
        tracemalloc.start()

    try:
        yield
    finally:
        end = time.time()
        end_mem = get_process_memory_mb()
        peak_mem = get_peak_memory_mb()
        duration_ms = (end - start) * 1000

        logger.info(
            f"Profile [{label}]: "
            f"Duration={duration_ms:.2f}ms, "
            f"PeakMem={peak_mem:.2f}MB, "
            f"StartMem={start_mem:.2f}MB, EndMem={end_mem:.2f}MB"
        )

def profile_function(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to profile a function's execution time and memory."""
    def wrapper(*args: Any, **kwargs: Any) -> T:
        start = time.time()
        if not tracemalloc.is_tracing():
            tracemalloc.start()

        try:
            result = func(*args, **kwargs)
        finally:
            end = time.time()
            peak_mem = get_peak_memory_mb()
            duration_ms = (end - start) * 1000
            logger.info(
                f"Function [{func.__name__}]: "
                f"Duration={duration_ms:.2f}ms, PeakMem={peak_mem:.2f}MB"
            )

        return result

    return wrapper


def reset_profiling() -> None:
    """Reset the profiler state."""
    if tracemalloc.is_tracing():
        tracemalloc.stop()
    logger.debug("Profiling reset")


def measure_execution(func: Callable[..., T]) -> ProfileResult:
    """Measure execution time and memory for a function call."""
    start_time = time.time()
    if not tracemalloc.is_tracing():
        tracemalloc.start()

    result = func()

    end_time = time.time()
    peak_memory = get_peak_memory_mb()
    duration_ms = (end_time - start_time) * 1000

    return ProfileResult(
        start_time=start_time,
        end_time=end_time,
        peak_memory_mb=peak_memory,
        duration_ms=duration_ms
    )
