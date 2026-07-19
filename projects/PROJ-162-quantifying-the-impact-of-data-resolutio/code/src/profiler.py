"""
Memory and CPU profiling utilities for the gravitational wave analysis pipeline.

Implements FR-006: Hard memory limit enforcement with logging and abort mechanisms.
"""
import os
import sys
import time
import json
import threading
import resource
import logging
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass, asdict
from contextlib import contextmanager

# Configure logging for profiling events
PROFILER_LOGGER = logging.getLogger("llmXive.profiler")
if not PROFILER_LOGGER.handlers:
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    PROFILER_LOGGER.addHandler(handler)
    PROFILER_LOGGER.setLevel(logging.INFO)

# Project paths relative to root
# We assume this file is at code/src/profiler.py, so data/ is at ../../data/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_PROFILING_DIR = _PROJECT_ROOT / "data" / "profiling"
_MEMORY_ERROR_LOG = _PROFILING_DIR / "memory_error.log"

# Hard memory limit in GB (FR-006 requirement)
MEMORY_LIMIT_GB = 6.0
MEMORY_LIMIT_BYTES = int(MEMORY_LIMIT_GB * 1024 ** 3)

class ProfilerError(Exception):
    """Base exception for profiler errors."""
    pass

class MemoryLimitExceededError(ProfilerError):
    """Raised when memory usage exceeds the hard limit."""
    def __init__(self, current_mb: float, limit_mb: float):
        self.current_mb = current_mb
        self.limit_mb = limit_mb
        super().__init__(
            f"Memory limit exceeded: {current_mb:.2f} MB > {limit_mb:.2f} MB"
        )

@dataclass
class ResourceMetrics:
    """Container for resource usage metrics."""
    peak_memory_mb: float
    current_memory_mb: float
    cpu_time_seconds: float
    timestamp: str
    batch_id: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class Profiler:
    """
    Context manager and utility class for monitoring resource usage.
    Enforces hard memory limits and logs violations.
    """

    def __init__(self, batch_id: Optional[str] = None, limit_gb: float = MEMORY_LIMIT_GB):
        self.batch_id = batch_id
        self.limit_bytes = int(limit_gb * 1024 ** 3)
        self.limit_mb = limit_gb
        self.start_time: Optional[float] = None
        self.start_memory: float = 0.0
        self.peak_memory: float = 0.0
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()

    def _get_current_memory_mb(self) -> float:
        """Get current process memory usage in MB."""
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, bytes on macOS. Detect platform.
        if sys.platform == "darwin":
            return usage.ru_maxrss / (1024 * 1024)
        else:
            return usage.ru_maxrss / 1024.0

    def _monitor_loop(self):
        """Background thread to monitor memory usage periodically."""
        while not self._stop_monitoring.is_set():
            current_mb = self._get_current_memory_mb()
            if current_mb > self.peak_memory:
                self.peak_memory = current_mb
            
            if current_mb > self.limit_mb:
                self._handle_limit_exceeded(current_mb)
                break
            time.sleep(0.1)  # Check every 100ms

    def _handle_limit_exceeded(self, current_mb: float):
        """Handle memory limit violation: log, record, and raise."""
        self._stop_monitoring.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
        
        # Ensure profiling directory exists
        _PROFILING_DIR.mkdir(parents=True, exist_ok=True)
        
        error_msg = f"BATCH {self.batch_id}: Memory limit exceeded. Peak: {current_mb:.2f} MB. Limit: {self.limit_mb:.2f} MB. Timestamp: {time.strftime('%Y-%m-%dT%H:%M:%S')}"
        
        # Write detailed log to memory_error.log
        try:
            with open(_MEMORY_ERROR_LOG, "a") as f:
                f.write(f"{error_msg}\n")
                f.write("-" * 80 + "\n")
                # Dump additional context if available
                f.write(f"Peak memory recorded: {self.peak_memory:.2f} MB\n")
                f.write(f"Current process ID: {os.getpid()}\n")
                f.write("-" * 80 + "\n\n")
        except IOError as e:
            PROFILER_LOGGER.error(f"Failed to write memory error log: {e}")
        
        PROFILER_LOGGER.critical(error_msg)
        raise MemoryLimitExceededError(current_mb, self.limit_mb)

    def start(self):
        """Start memory monitoring."""
        self.start_time = time.time()
        self.start_memory = self._get_current_memory_mb()
        self.peak_memory = self.start_memory
        self._stop_monitoring.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        self._monitoring = True
        PROFILER_LOGGER.info(f"Profiler started for batch {self.batch_id}. Limit: {self.limit_mb:.2f} MB")

    def stop(self) -> ResourceMetrics:
        """Stop monitoring and return metrics."""
        if self._monitoring:
            self._stop_monitoring.set()
            if self._monitor_thread:
                self._monitor_thread.join(timeout=1.0)
            self._monitoring = False

        current_mb = self._get_current_memory_mb()
        if current_mb > self.peak_memory:
            self.peak_memory = current_mb

        cpu_time = time.time() - (self.start_time or time.time())
        
        metrics = ResourceMetrics(
            peak_memory_mb=self.peak_memory,
            current_memory_mb=current_mb,
            cpu_time_seconds=cpu_time,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            batch_id=self.batch_id
        )
        
        PROFILER_LOGGER.info(
            f"Profiler stopped. Batch {self.batch_id}: Peak {self.peak_memory:.2f} MB, "
            f"Current {current_mb:.2f} MB, CPU {cpu_time:.2f}s"
        )
        return metrics

    @contextmanager
    def __call__(self, batch_id: Optional[str] = None):
        """Context manager usage: with profiler() as p: ..."""
        ctx_batch_id = batch_id or self.batch_id
        p = Profiler(batch_id=ctx_batch_id, limit_gb=self.limit_mb / 1024 ** 3 * 1024 ** 3) # Keep same limit
        p.start()
        try:
            yield p
        finally:
            p.stop()

def get_peak_memory_mb() -> float:
    """Get the current peak memory usage for the process in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    if sys.platform == "darwin":
        return usage.ru_maxrss / (1024 * 1024)
    else:
        return usage.ru_maxrss / 1024.0

def check_memory_limit(limit_mb: float = MEMORY_LIMIT_GB * 1024) -> None:
    """
    Check if current memory usage exceeds the limit.
    Raises MemoryLimitExceededError if violated.
    """
    current = get_peak_memory_mb()
    if current > limit_mb:
        # Ensure directory exists before logging
        _PROFILING_DIR.mkdir(parents=True, exist_ok=True)
        error_msg = f"Memory limit exceeded: {current:.2f} MB > {limit_mb:.2f} MB"
        try:
            with open(_MEMORY_ERROR_LOG, "a") as f:
                f.write(f"{error_msg} (Check called at {time.strftime('%Y-%m-%dT%H:%M:%S')})\n")
        except IOError:
            pass
        raise MemoryLimitExceededError(current, limit_mb)

@contextmanager
def profile_block(block_name: str, limit_mb: float = MEMORY_LIMIT_GB * 1024):
    """
    Context manager to profile a specific code block.
    Checks memory limit at entry and exit.
    """
    start_mem = get_peak_memory_mb()
    start_time = time.time()
    PROFILER_LOGGER.debug(f"Entering block: {block_name}, Start Mem: {start_mem:.2f} MB")
    try:
        yield
    finally:
        end_mem = get_peak_memory_mb()
        elapsed = time.time() - start_time
        PROFILER_LOGGER.debug(
            f"Exited block: {block_name}, End Mem: {end_mem:.2f} MB, "
            f"Delta: {end_mem - start_mem:.2f} MB, Time: {elapsed:.3f}s"
        )
        check_memory_limit(limit_mb)

@contextmanager
def profile_function(func: Callable, limit_mb: float = MEMORY_LIMIT_GB * 1024):
    """
    Decorator-like context manager to profile a function call.
    """
    start_mem = get_peak_memory_mb()
    start_time = time.time()
    func_name = func.__name__
    try:
        result = func()
        return result
    finally:
        end_mem = get_peak_memory_mb()
        elapsed = time.time() - start_time
        PROFILER_LOGGER.info(
            f"Function {func_name} completed. Peak Mem: {end_mem:.2f} MB, "
            f"Duration: {elapsed:.3f}s"
        )
        check_memory_limit(limit_mb)

def profile(func: Callable, limit_mb: float = MEMORY_LIMIT_GB * 1024) -> Callable:
    """Decorator to profile a function with memory limit enforcement."""
    def wrapper(*args, **kwargs):
        start_mem = get_peak_memory_mb()
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_mem = get_peak_memory_mb()
            elapsed = time.time() - start_time
            PROFILER_LOGGER.info(
                f"Function {func.__name__} executed. Peak Mem: {end_mem:.2f} MB, "
                f"Duration: {elapsed:.3f}s"
            )
            check_memory_limit(limit_mb)
    return wrapper

def main():
    """CLI entry point for basic profiler testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Profiler CLI")
    parser.add_argument("--limit", type=float, default=MEMORY_LIMIT_GB, help="Memory limit in GB")
    parser.add_argument("--batch", type=str, default=None, help="Batch ID for logging")
    args = parser.parse_args()

    try:
        profiler = Profiler(batch_id=args.batch, limit_gb=args.limit)
        with profiler():
            # Simulate some work
            data = []
            for i in range(1000000):
                data.append([i] * 100)
            # Force garbage collection to see real peak
            import gc
            gc.collect()
            
            metrics = profiler.stop()
            print(f"Profiling complete. Peak Memory: {metrics.peak_memory_mb:.2f} MB")
            print(f"CPU Time: {metrics.cpu_time_seconds:.2f} s")
            
            # Save metrics to a file for verification
            metrics_path = _PROFILING_DIR / "last_run_metrics.json"
            with open(metrics_path, "w") as f:
                json.dump(metrics.to_dict(), f, indent=2)
            print(f"Metrics saved to {metrics_path}")
            
    except MemoryLimitExceededError as e:
        print(f"FATAL: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()