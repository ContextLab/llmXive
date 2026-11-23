"""
Memory monitoring utilities for enforcing RAM limits during training.

This module provides tools to track RAM usage and enforce a memory limit,
ensuring training runs stay within the 7GB constraint specified in the project.
"""

import os
import gc
import time
import threading
from typing import Optional, Callable, Any, Dict, List
from contextlib import contextmanager

# Try to import psutil for accurate memory measurement
# If not available, fall back to /proc on Linux or basic estimation
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Platform-specific imports for fallback
if os.name == 'posix':
    try:
        from resource import getrusage, RUSAGE_SELF
        HAS_RESOURCE = True
    except ImportError:
        HAS_RESOURCE = False
else:
    HAS_RESOURCE = False


class MemoryMonitor:
    """
    Monitors memory usage of the current process.

    Attributes:
        limit_bytes (int): Memory limit in bytes.
        history (List[Dict]): List of recorded memory snapshots.
        peak_bytes (int): Peak memory usage observed.
        _thread (threading.Thread): Background monitoring thread.
        _stop_event (threading.Event): Event to signal thread stop.
    """

    def __init__(self, limit_mb: float = 7000, sample_interval: float = 0.1):
        """
        Initialize the memory monitor.

        Args:
            limit_mb: Memory limit in megabytes (default 7000MB = 7GB).
            sample_interval: Interval in seconds between memory samples.
        """
        self.limit_bytes = int(limit_mb * 1024 * 1024)
        self.sample_interval = sample_interval
        self.history: List[Dict[str, Any]] = []
        self.peak_bytes: int = 0
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._start_time: Optional[float] = None

    def _get_memory_usage(self) -> int:
        """
        Get current memory usage in bytes.

        Returns:
            Current memory usage in bytes.
        """
        if HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        elif HAS_RESOURCE:
            # Fallback for Linux/Unix using resource module
            usage = getrusage(RUSAGE_SELF)
            # ru_maxrss is in kilobytes on Linux, bytes on macOS
            if os.uname().sysname == 'Darwin':
                return usage.ru_maxrss
            else:
                return usage.ru_maxrss * 1024
        else:
            # Last resort: return 0 or raise error
            # For safety, we raise an error if no method is available
            raise RuntimeError(
                "No memory measurement backend available. "
                "Install 'psutil' or run on a supported POSIX system."
            )

    def start(self) -> None:
        """Start background monitoring thread."""
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._start_time = time.time()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop background monitoring thread."""
        if self._thread is None:
            return

        self._stop_event.set()
        self._thread.join(timeout=2.0)
        self._thread = None

    def _monitor_loop(self) -> None:
        """Background loop to sample memory usage."""
        while not self._stop_event.is_set():
            try:
                current_mem = self._get_memory_usage()
                self.history.append({
                    'timestamp': time.time(),
                    'elapsed': time.time() - (self._start_time or time.time()),
                    'memory_bytes': current_mem
                })
                if current_mem > self.peak_bytes:
                    self.peak_bytes = current_mem

                # Check limit
                if current_mem > self.limit_bytes:
                    # Force garbage collection
                    gc.collect()
                    # Re-check after GC
                    current_mem = self._get_memory_usage()
                    if current_mem > self.limit_bytes:
                        # Log but don't stop - let the context manager or caller handle it
                        pass

            except Exception:
                # Silently ignore errors in background thread
                pass

            self._stop_event.wait(self.sample_interval)

    def get_current_memory_bytes(self) -> int:
        """Get current memory usage."""
        return self._get_memory_usage()

    def get_peak_memory_bytes(self) -> int:
        """Get peak memory usage since start."""
        return max(self.peak_bytes, self._get_memory_usage())

    def get_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        return self.get_current_memory_bytes() / (1024 * 1024)

    def get_peak_memory_mb(self) -> float:
        """Get peak memory usage in MB."""
        return self.get_peak_memory_bytes() / (1024 * 1024)

    def is_over_limit(self) -> bool:
        """Check if current memory usage exceeds the limit."""
        return self.get_current_memory_bytes() > self.limit_bytes

    def get_history(self) -> List[Dict[str, Any]]:
        """Get memory history."""
        return self.history.copy()

    def reset(self) -> None:
        """Reset monitor state."""
        self.history.clear()
        self.peak_bytes = 0
        self._start_time = time.time()


@contextmanager
def memory_limit_context(
    limit_mb: float = 7000,
    monitor: Optional[MemoryMonitor] = None,
    strict: bool = True
):
    """
    Context manager to enforce a memory limit.

    Args:
        limit_mb: Memory limit in MB.
        monitor: Optional existing MemoryMonitor instance.
        strict: If True, raises MemoryError when limit exceeded.

    Yields:
        MemoryMonitor instance.

    Raises:
        MemoryError: If strict mode and memory limit exceeded.
    """
    if monitor is None:
        monitor = MemoryMonitor(limit_mb=limit_mb)

    monitor.start()
    try:
        yield monitor
        # Final check on exit
        if strict and monitor.is_over_limit():
            raise MemoryError(
                f"Memory limit exceeded: {monitor.get_memory_mb():.2f}MB "
                f"> {limit_mb}MB"
            )
    except MemoryError:
        raise
    except Exception:
        raise
    finally:
        monitor.stop()
        gc.collect()


def enforce_memory_limit(
    limit_mb: float = 7000,
    check_interval: float = 0.5,
    callback: Optional[Callable[[float], None]] = None
) -> MemoryMonitor:
    """
    Enforce a memory limit with periodic checks.

    This function starts a background monitor and can optionally call
    a callback function when memory usage exceeds a threshold.

    Args:
        limit_mb: Memory limit in MB.
        check_interval: Interval between checks in seconds.
        callback: Optional callback function that receives memory usage in MB.

    Returns:
        Running MemoryMonitor instance.
    """
    monitor = MemoryMonitor(limit_mb=limit_mb, sample_interval=check_interval)
    monitor.start()

    # Start a watcher thread if callback is provided
    if callback is not None:
        def watcher():
            while not monitor._stop_event.is_set():
                current_mb = monitor.get_memory_mb()
                if current_mb > limit_mb * 0.9:  # 90% threshold
                    callback(current_mb)
                monitor._stop_event.wait(check_interval)

        watcher_thread = threading.Thread(target=watcher, daemon=True)
        watcher_thread.start()

    return monitor


def main() -> None:
    """
    Main function for testing the memory monitor.
    """
    print("Memory Monitor Test")
    print("=" * 40)

    monitor = MemoryMonitor(limit_mb=7000, sample_interval=0.1)
    monitor.start()

    # Simulate some memory usage
    data = []
    for i in range(100):
        data.append([j * 1.5 for j in range(10000)])
        time.sleep(0.1)

        if monitor.is_over_limit():
            print(f"Warning: Memory limit exceeded at iteration {i}")
            break

    monitor.stop()

    print(f"Peak memory: {monitor.get_peak_memory_mb():.2f} MB")
    print(f"Final memory: {monitor.get_memory_mb():.2f} MB")
    print(f"Sample count: {len(monitor.get_history())}")

    # Demonstrate context manager
    print("\nTesting context manager...")
    with memory_limit_context(limit_mb=7000) as ctx:
        # Simulate work
        _ = [0] * 1000000
        print(f"Memory in context: {ctx.get_memory_mb():.2f} MB")


if __name__ == "__main__":
    main()
