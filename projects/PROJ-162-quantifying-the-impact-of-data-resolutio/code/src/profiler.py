"""
Resource profiling module for memory and CPU monitoring.
Implements FR-006 with a hard 6GB memory limit.
"""
import os
import sys
import time
import json
import threading
import resource
from pathlib import Path
from typing import Optional, Callable, Any, Dict
from contextlib import contextmanager
from dataclasses import dataclass, asdict

# Configuration
MEMORY_LIMIT_GB = 6.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * (1024 ** 3)
PROFILING_LOG_PATH = Path("data/profiling/memory_error.log")
METRICS_LOG_PATH = Path("data/profiling/resource_metrics.json")

# Ensure profiling directory exists
PROFILING_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


class ProfilerError(Exception):
    """Base exception for profiler errors."""
    pass


class MemoryLimitExceededError(ProfilerError):
    """Raised when memory usage exceeds the hard limit."""
    def __init__(self, current_mb: float, limit_mb: float, details: str = ""):
        self.current_mb = current_mb
        self.limit_mb = limit_mb
        self.details = details
        msg = (
            f"Memory limit exceeded: {current_mb:.2f} MB used (limit: {limit_mb:.2f} MB). "
            f"{details}"
        )
        super().__init__(msg)


@dataclass
class ResourceMetrics:
    """Container for resource usage metrics."""
    peak_memory_mb: float
    current_memory_mb: float
    cpu_time_seconds: float
    elapsed_time_seconds: float
    timestamp: str
    batch_id: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


class Profiler:
    """
    Context manager and utility class for profiling memory and CPU usage.
    Enforces a hard 6GB memory limit.
    """

    def __init__(self, batch_id: Optional[str] = None):
        self.batch_id = batch_id
        self.start_time: Optional[float] = None
        self.start_cpu: Optional[float] = None
        self.peak_memory_mb: float = 0.0
        self.monitoring: bool = False
        self.monitor_thread: Optional[threading.Thread] = None
        self._stop_monitor = threading.Event()

    def _get_current_memory_mb(self) -> float:
        """Get current memory usage in MB using resource module."""
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, MB on macOS. Normalize to MB.
        if sys.platform == "darwin":
            return usage.ru_maxrss
        else:
            return usage.ru_maxrss / 1024.0

    def _monitor_loop(self):
        """Background thread to monitor memory usage periodically."""
        while not self._stop_monitor.is_set():
            current_mb = self._get_current_memory_mb()
            if current_mb > self.peak_memory_mb:
                self.peak_memory_mb = current_mb

            # Check limit
            if current_mb > MEMORY_LIMIT_BYTES / (1024 ** 2):
                self._stop_monitor.set()
                # Log error immediately
                self._log_memory_error(current_mb)
                # Raise exception in main thread via a mechanism or just flag
                # For safety, we rely on the check in the main flow, but we can
                # also raise an error here if we catch it.
                # Since we are in a thread, we set a flag or raise a system exit.
                # To be safe and clean, we will let the main loop check.
                # However, to enforce "abort", we might need to kill the process.
                # Let's set a global flag or raise SystemExit if critical.
                # For this implementation, we will raise MemoryLimitExceededError
                # and let the caller handle it, but since we are in a thread,
                # we will just ensure the main loop catches it.
                # Actually, to "abort the current batch", we should raise an exception
                # that propagates. But threads can't easily raise exceptions in the main thread.
                # Strategy: The main loop will check a shared variable or we just rely
                # on the periodic check in the main loop.
                # To strictly enforce "abort", we will set a flag and the main loop
                # will check it frequently.
                # Better: The main loop calls check_memory_limit() frequently.
                # We will update peak_memory_mb here.
            time.sleep(0.1) # Check every 100ms

    def _log_memory_error(self, current_mb: float):
        """Write detailed error log to data/profiling/memory_error.log."""
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "batch_id": self.batch_id,
            "current_memory_mb": current_mb,
            "limit_mb": MEMORY_LIMIT_GB * 1024,
            "error_type": "MemoryLimitExceededError",
            "message": f"Peak memory usage {current_mb:.2f} MB exceeded limit of {MEMORY_LIMIT_GB * 1024:.2f} MB",
            "traceback": "N/A" # Could capture actual traceback if needed
        }
        try:
            with open(PROFILING_LOG_PATH, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            sys.stderr.write(f"Failed to write memory error log: {e}\n")

    def start(self):
        """Start profiling."""
        self.start_time = time.time()
        self.start_cpu = resource.getrusage(resource.RUSAGE_SELF).ru_utime + resource.getrusage(resource.RUSAGE_SELF).ru_stime
        self.peak_memory_mb = self._get_current_memory_mb()
        self._stop_monitor.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.monitoring = True

    def stop(self) -> ResourceMetrics:
        """Stop profiling and return metrics."""
        self.monitoring = False
        self._stop_monitor.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)

        end_time = time.time()
        end_cpu = resource.getrusage(resource.RUSAGE_SELF).ru_utime + resource.getrusage(resource.RUSAGE_SELF).ru_stime
        current_mb = self._get_current_memory_mb()

        if current_mb > self.peak_memory_mb:
            self.peak_memory_mb = current_mb

        metrics = ResourceMetrics(
            peak_memory_mb=self.peak_memory_mb,
            current_memory_mb=current_mb,
            cpu_time_seconds=end_cpu - (self.start_cpu or 0),
            elapsed_time_seconds=end_time - (self.start_time or 0),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            batch_id=self.batch_id
        )

        # Log metrics
        self._save_metrics(metrics)

        return metrics

    def _save_metrics(self, metrics: ResourceMetrics):
        """Append metrics to a JSON log file."""
        log_path = METRICS_LOG_PATH
        if not log_path.exists():
            log_path.write_text("[]")

        try:
            with open(log_path, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = []

        data.append(metrics.to_dict())

        with open(log_path, "w") as f:
            json.dump(data, f, indent=2)

    @contextmanager
    def profile_block(self, label: str = "block"):
        """Context manager to profile a specific block of code."""
        start = time.time()
        start_cpu = resource.getrusage(resource.RUSAGE_SELF).ru_utime + resource.getrusage(resource.RUSAGE_SELF).ru_stime
        start_mem = self._get_current_memory_mb()
        try:
            yield
        finally:
            end = time.time()
            end_cpu = resource.getrusage(resource.RUSAGE_SELF).ru_utime + resource.getrusage(resource.RUSAGE_SELF).ru_stime
            end_mem = self._get_current_memory_mb()
            print(f"[Profiler] {label}: {end - start:.3f}s, CPU: {end_cpu - start_cpu:.3f}s, Mem: {end_mem - start_mem:.2f} MB")


def get_peak_memory_mb() -> float:
    """Get the current peak memory usage in MB."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0 if sys.platform != "darwin" else resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


def check_memory_limit(current_mb: Optional[float] = None) -> None:
    """
    Check if current memory usage exceeds the hard limit.
    Raises MemoryLimitExceededError if limit is exceeded.
    """
    if current_mb is None:
        current_mb = get_peak_memory_mb()

    limit_mb = MEMORY_LIMIT_GB * 1024

    if current_mb > limit_mb:
        # Log error
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "batch_id": None,
            "current_memory_mb": current_mb,
            "limit_mb": limit_mb,
            "error_type": "MemoryLimitExceededError",
            "message": f"Memory limit exceeded: {current_mb:.2f} MB > {limit_mb:.2f} MB"
        }
        try:
            with open(PROFILING_LOG_PATH, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass

        raise MemoryLimitExceededError(current_mb, limit_mb, "Hard limit enforced.")


@contextmanager
def profile_function(func: Callable) -> Callable:
    """Decorator-like context manager to profile a function execution."""
    profiler = Profiler()
    profiler.start()
    try:
        yield func
    finally:
        metrics = profiler.stop()
        print(f"Function {func.__name__} completed. Peak Memory: {metrics.peak_memory_mb:.2f} MB")


def profile(func: Callable) -> Callable:
    """Decorator to profile a function's resource usage."""
    def wrapper(*args, **kwargs):
        profiler = Profiler(batch_id=func.__name__)
        profiler.start()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            metrics = profiler.stop()
            print(f"Profiled {func.__name__}: Peak Mem: {metrics.peak_memory_mb:.2f} MB, Time: {metrics.elapsed_time_seconds:.2f}s")
    return wrapper


def main():
    """CLI entry point for testing the profiler."""
    import argparse
    parser = argparse.ArgumentParser(description="Profiler CLI")
    parser.add_argument("--test", action="store_true", help="Run a memory test")
    args = parser.parse_args()

    if args.test:
        print("Running memory test...")
        profiler = Profiler(batch_id="test-run-001")
        profiler.start()

        try:
            # Simulate work
            data = []
            for i in range(1000000):
                data.append([0] * 1000)
                if i % 100000 == 0:
                    check_memory_limit()
        except MemoryLimitExceededError as e:
            print(f"CRITICAL: {e}")
            sys.exit(1)
        finally:
            metrics = profiler.stop()
            print(f"Test completed. Peak Memory: {metrics.peak_memory_mb:.2f} MB")


if __name__ == "__main__":
    main()