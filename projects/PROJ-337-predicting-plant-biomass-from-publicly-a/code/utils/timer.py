"""
Runtime timer and resource monitoring utilities.

Provides context managers and functions to measure execution time
and track CPU/memory usage for performance-critical sections.
"""
import os
import time
import resource
from contextlib import contextmanager
from typing import Generator, Optional, Dict, Any
from pathlib import Path

from code.utils.logger import get_logger
from code.utils.config import get_config

logger = get_logger(__name__)


class Timer:
    """
    A context manager and utility class for measuring execution time
    and resource usage (CPU time, wall time, memory).
    """

    def __init__(self, label: str = "Timer"):
        self.label = label
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.start_cpu: float = 0.0
        self.end_cpu: float = 0.0
        self.start_memory: int = 0
        self.end_memory: int = 0
        self.elapsed_wall: float = 0.0
        self.elapsed_cpu: float = 0.0
        self.memory_delta: int = 0

    def __enter__(self) -> "Timer":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
        self.log()

    def start(self) -> None:
        """Start the timer and record initial resource usage."""
        self.start_time = time.perf_counter()
        self.start_cpu = time.process_time()
        try:
            # Usage returns (utime, stime) in seconds
            usage = resource.getrusage(resource.RUSAGE_SELF)
            self.start_memory = usage.ru_maxrss * 1024  # Convert KB to bytes (Linux)
        except Exception:
            # Fallback if resource usage not available (e.g., Windows)
            self.start_memory = 0
            logger.warning(f"Could not retrieve start memory usage for {self.label}")

    def stop(self) -> None:
        """Stop the timer and record final resource usage."""
        self.end_time = time.perf_counter()
        self.end_cpu = time.process_time()
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            self.end_memory = usage.ru_maxrss * 1024
        except Exception:
            self.end_memory = 0
            logger.warning(f"Could not retrieve end memory usage for {self.label}")

        self.elapsed_wall = self.end_time - self.start_time
        self.elapsed_cpu = self.end_cpu - self.start_cpu
        self.memory_delta = self.end_memory - self.start_memory

    def log(self) -> None:
        """Log the timing and resource statistics."""
        msg = (
            f"[{self.label}] "
            f"Wall time: {self.elapsed_wall:.4f}s, "
            f"CPU time: {self.elapsed_cpu:.4f}s"
        )
        if self.start_memory > 0:
            msg += f", Memory delta: {self.memory_delta / (1024*1024):.2f} MB"
        logger.info(msg)

    def to_dict(self) -> Dict[str, Any]:
        """Return timing stats as a dictionary."""
        return {
            "label": self.label,
            "wall_time_seconds": self.elapsed_wall,
            "cpu_time_seconds": self.elapsed_cpu,
            "memory_delta_bytes": self.memory_delta,
            "memory_delta_mb": self.memory_delta / (1024 * 1024) if self.memory_delta > 0 else 0.0
        }


@contextmanager
def timed_operation(label: str = "Operation") -> Generator[Timer, None, None]:
    """
    Context manager to time a block of code.

    Usage:
        with timed_operation("My Task") as timer:
            do_work()
        # timer.elapsed_wall is available here
    """
    timer = Timer(label)
    try:
        yield timer
    finally:
        timer.stop()
        timer.log()


def get_current_memory_usage_mb() -> float:
    """
    Get the current peak resident set size (RSS) of the process in MB.
    """
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, bytes on some others; assume KB for safety
        return usage.ru_maxrss / 1024.0
    except Exception:
        return 0.0


def get_wall_time_elapsed(start_time: float) -> float:
    """Calculate elapsed wall time from a start timestamp."""
    return time.perf_counter() - start_time


def main() -> None:
    """
    Demo function to verify timer functionality.
    """
    logger.info("Running timer demo...")
    
    # Test 1: Simple wall time
    with timed_operation("Demo Sleep") as t:
        time.sleep(0.5)
    
    assert t.elapsed_wall >= 0.4, "Sleep test failed"
    logger.info(f"Demo Sleep completed in {t.elapsed_wall:.4f}s")

    # Test 2: Resource tracking
    with timed_operation("Demo Compute") as t:
        _ = sum(i * i for i in range(10_000_000))
    
    logger.info(f"Demo Compute stats: {t.to_dict()}")
    logger.info("Timer demo successful.")


if __name__ == "__main__":
    main()