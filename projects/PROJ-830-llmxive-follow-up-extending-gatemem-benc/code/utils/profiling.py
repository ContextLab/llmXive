import os
import time
import tracemalloc
import logging
from typing import Optional, Dict, Any, Callable, TypeVar, ContextManager
from contextlib import contextmanager
from dataclasses import dataclass, field

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from code.logging_config import setup_logging

logger = setup_logging(__name__)

@dataclass
class ProfileResult:
    """Container for profiling metrics."""
    start_time: float
    end_time: float
    duration_ms: float
    peak_memory_mb: float
    current_memory_mb: float
    block_name: Optional[str] = None

class ProfileContext:
    """
    Context manager for profiling CPU/RAM and wall-clock time.
    Uses tracemalloc for memory and time.time() for wall-clock.
    Falls back to psutil for memory if tracemalloc is unavailable or insufficient.
    """
    def __init__(self, block_name: str = "unnamed"):
        self.block_name = block_name
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.peak_memory_mb: float = 0.0
        self.current_memory_mb: float = 0.0
        self._tracemalloc_started: bool = False

    def _get_memory_mb(self) -> float:
        """Get current process memory in MB."""
        if HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            # rss is Resident Set Size
            return process.memory_info().rss / (1024 * 1024)
        elif tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            return current / (1024 * 1024)
        else:
            return 0.0

    def _get_peak_memory_mb(self) -> float:
        """Get peak process memory in MB."""
        if HAS_PSUTIL:
            # psutil doesn't track peak RSS easily without custom logic,
            # so we rely on tracemalloc if available, otherwise estimate.
            if tracemalloc.is_tracing():
                _, peak = tracemalloc.get_traced_memory()
                return peak / (1024 * 1024)
            # Fallback: current is a safe lower bound estimate
            return self._get_memory_mb()
        elif tracemalloc.is_tracing():
            _, peak = tracemalloc.get_traced_memory()
            return peak / (1024 * 1024)
        else:
            return 0.0

    def __enter__(self) -> "ProfileContext":
        self.start_time = time.time()
        if not tracemalloc.is_tracing():
            tracemalloc.start()
            self._tracemalloc_started = True
        else:
            self._tracemalloc_started = False
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.current_memory_mb = self._get_memory_mb()
        self.peak_memory_mb = self._get_peak_memory_mb()
        
        duration = self.end_time - self.start_time
        self.duration_ms = duration * 1000

        result = ProfileResult(
            start_time=self.start_time,
            end_time=self.end_time,
            duration_ms=self.duration_ms,
            peak_memory_mb=self.peak_memory_mb,
            current_memory_mb=self.current_memory_mb,
            block_name=self.block_name
        )
        
        log_metrics(result)
        
        if self._tracemalloc_started:
            tracemalloc.stop()

    def get_result(self) -> ProfileResult:
        """Manually retrieve results if not using context manager exit."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.current_memory_mb = self._get_memory_mb()
        self.peak_memory_mb = self._get_peak_memory_mb()
        return ProfileResult(
            start_time=self.start_time,
            end_time=self.end_time,
            duration_ms=self.duration_ms,
            peak_memory_mb=self.peak_memory_mb,
            current_memory_mb=self.current_memory_mb,
            block_name=self.block_name
        )

def log_metrics(result: ProfileResult) -> None:
    """
    Log profiling metrics to the configured logger.
    Format: [PROFILING] <block_name>: <duration_ms>ms, <peak_memory_mb>MB peak.
    """
    msg = (
        f"[PROFILING] {result.block_name}: "
        f"{result.duration_ms:.2f}ms wall-clock, "
        f"{result.peak_memory_mb:.2f}MB peak RAM"
    )
    logger.info(msg)

@contextmanager
def profile_block(name: str = "block") -> ContextManager[ProfileContext]:
    """Context manager to profile a specific code block."""
    ctx = ProfileContext(block_name=name)
    try:
        yield ctx
    finally:
        pass  # Logging happens in __exit__

def profile_function(func: Callable) -> Callable:
    """Decorator to profile a function's execution time and memory."""
    def wrapper(*args, **kwargs):
        with ProfileContext(block_name=func.__name__) as ctx:
            result = func(*args, **kwargs)
        return result
    return wrapper

def start_profiling() -> None:
    """Start global tracing if not already started."""
    if not tracemalloc.is_tracing():
        tracemalloc.start()
        logger.info("Tracemalloc started for global profiling.")

def stop_profiling() -> None:
    """Stop global tracing."""
    if tracemalloc.is_tracing():
        tracemalloc.stop()
        logger.info("Tracemalloc stopped.")

def reset_profiling() -> None:
    """Reset tracing to clear accumulated memory stats."""
    if tracemalloc.is_tracing():
        tracemalloc.stop()
    tracemalloc.start()
    logger.info("Tracemalloc reset.")

def get_process_memory_mb() -> float:
    """Utility to get current process memory in MB."""
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    elif tracemalloc.is_tracing():
        current, _ = tracemalloc.get_traced_memory()
        return current / (1024 * 1024)
    return 0.0

def get_peak_memory_mb() -> float:
    """Utility to get peak process memory in MB."""
    if tracemalloc.is_tracing():
        _, peak = tracemalloc.get_traced_memory()
        return peak / (1024 * 1024)
    return 0.0

def measure_execution(func: Callable, *args, **kwargs) -> Tuple[float, Any]:
    """
    Measure execution time and memory of a function call.
    Returns (duration_ms, result).
    """
    start = time.time()
    if not tracemalloc.is_tracing():
        tracemalloc.start()
        reset = True
    else:
        reset = False
    
    result = func(*args, **kwargs)
    
    end = time.time()
    duration = (end - start) * 1000
    _, peak = tracemalloc.get_traced_memory()
    peak_mb = peak / (1024 * 1024)
    
    if reset:
        tracemalloc.stop()
        
    logger.info(f"[MEASURE] {func.__name__}: {duration:.2f}ms, {peak_mb:.2f}MB peak")
    return duration, result

def main():
    """Demo execution for profiling module."""
    logger.info("Starting profiling demo...")
    
    with ProfileContext("demo_block") as ctx:
        # Simulate work
        data = [i * i for i in range(1000000)]
        _ = sum(data)
    
    logger.info(f"Demo completed. Peak RAM: {ctx.peak_memory_mb:.2f}MB")

if __name__ == "__main__":
    main()