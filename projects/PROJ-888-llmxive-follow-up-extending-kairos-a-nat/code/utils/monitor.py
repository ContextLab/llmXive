"""
Resource monitoring utilities for llmXive.

Provides functions to track RAM usage, CPU utilization, and elapsed time.
Includes a context manager for automatic monitoring and validation against
resource limits.
"""
import os
import time
import threading
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import psutil

# Process object for the current process
_PROCESS = psutil.Process(os.getpid())


@dataclass
class ResourceSnapshot:
    """A snapshot of resource usage at a specific point in time."""
    timestamp: float
    ram_mb: float
    cpu_percent: float
    elapsed_time: float

@dataclass
class ResourceMonitor:
    """
    Monitors resource usage (RAM, CPU) over time.

    Attributes:
        start_time: Time when monitoring started (seconds since epoch).
        peak_memory_mb: Highest recorded RAM usage in MB.
        samples: List of ResourceSnapshot objects collected during monitoring.
        _thread: Background thread for sampling.
        _stop_event: Event to signal the background thread to stop.
    """
    start_time: float = field(default_factory=time.time)
    peak_memory_mb: float = 0.0
    samples: List[ResourceSnapshot] = field(default_factory=list)
    _thread: Optional[threading.Thread] = field(default=None, repr=False)
    _stop_event: threading.Event = field(default_factory=threading.Event, repr=False)
    _interval: float = 1.0  # Sampling interval in seconds

    def start(self) -> None:
        """Start the background monitoring thread."""
        if self._thread is not None and self._thread.is_alive():
            return  # Already running

        self.start_time = time.time()
        self.peak_memory_mb = 0.0
        self.samples = []
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._sample_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the background monitoring thread and return the final snapshot."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _sample_loop(self) -> None:
        """Background loop to collect resource samples."""
        while not self._stop_event.is_set():
            try:
                snapshot = self._take_snapshot()
                self.samples.append(snapshot)
                if snapshot.ram_mb > self.peak_memory_mb:
                    self.peak_memory_mb = snapshot.ram_mb
            except Exception:
                # Silently ignore sampling errors to avoid crashing the main thread
                pass
            time.sleep(self._interval)

    def _take_snapshot(self) -> ResourceSnapshot:
        """Take a single resource snapshot."""
        now = time.time()
        ram_mb = get_ram_usage()
        cpu_pct = get_cpu_utilization()
        elapsed = now - self.start_time
        return ResourceSnapshot(
            timestamp=now,
            ram_mb=ram_mb,
            cpu_percent=cpu_pct,
            elapsed_time=elapsed
        )

    def get_summary(self) -> Dict[str, Any]:
        """
        Return a summary of the monitoring session.

        Returns:
            Dictionary with start_time, end_time, duration_s,
            peak_memory_mb, avg_cpu_percent, sample_count.
        """
        if not self.samples:
            return {
                "start_time": self.start_time,
                "end_time": time.time(),
                "duration_s": time.time() - self.start_time,
                "peak_memory_mb": self.peak_memory_mb,
                "avg_cpu_percent": 0.0,
                "sample_count": 0
            }

        end_time = self.samples[-1].timestamp
        durations = [s.elapsed_time for s in self.samples]
        cpus = [s.cpu_percent for s in self.samples]

        return {
            "start_time": self.samples[0].timestamp,
            "end_time": end_time,
            "duration_s": end_time - self.samples[0].timestamp,
            "peak_memory_mb": self.peak_memory_mb,
            "avg_cpu_percent": sum(cpus) / len(cpus),
            "sample_count": len(self.samples)
        }


def get_ram_usage() -> float:
    """
    Get the current RAM usage of the process in Megabytes.

    Returns:
        Float representing RAM usage in MB.
    """
    mem_info = _PROCESS.memory_info()
    return mem_info.rss / (1024 * 1024)


def get_cpu_utilization() -> float:
    """
    Get the current CPU utilization of the process as a percentage.

    Returns:
        Float representing CPU percentage (0.0 to 100.0 * num_cpus).
    """
    # percent for the current process
    return _PROCESS.cpu_percent(interval=None)


def get_peak_memory_mb() -> float:
    """
    Get the peak RSS memory usage of the process since the start of the program.

    Returns:
        Float representing peak RAM usage in MB.
    """
    return _PROCESS.memory_info().peak_rss / (1024 * 1024) if hasattr(_PROCESS.memory_info(), 'peak_rss') else get_ram_usage()


def get_elapsed_time(start_time: Optional[float] = None) -> float:
    """
    Get the elapsed time since a given start time.

    Args:
        start_time: Start time in seconds since epoch. Defaults to time.time().

    Returns:
        Float representing elapsed seconds.
    """
    if start_time is None:
        start_time = time.time()
    return time.time() - start_time


def format_bytes(num_bytes: float) -> str:
    """
    Format a byte value into a human-readable string.

    Args:
        num_bytes: Value in bytes.

    Returns:
        String like "1.5 GB".
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"


def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds into a human-readable string.

    Args:
        seconds: Duration in seconds.

    Returns:
        String like "1h 23m 45s".
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def validate_resource_limits(peak_ram_gb: float, max_ram_gb: float = 7.0,
                             max_time_h: float = 6.0,
                             current_time_h: Optional[float] = None) -> Dict[str, Any]:
    """
    Validate resource usage against defined limits.

    Args:
        peak_ram_gb: Peak RAM usage in GB.
        max_ram_gb: Maximum allowed RAM in GB (default 7.0).
        max_time_h: Maximum allowed time in hours (default 6.0).
        current_time_h: Current elapsed time in hours. If None, calculated from start.

    Returns:
        Dictionary with 'status' ('pass' or 'fail'), 'reasons' (list of strings),
        and 'details' (dict with values).
    """
    reasons = []
    status = "pass"

    if peak_ram_gb > max_ram_gb:
        status = "fail"
        reasons.append(f"Peak RAM ({peak_ram_gb:.2f} GB) exceeds limit ({max_ram_gb} GB)")

    if current_time_h is not None and current_time_h > max_time_h:
        status = "fail"
        reasons.append(f"Elapsed time ({current_time_h:.2f} h) exceeds limit ({max_time_h} h)")

    return {
        "status": status,
        "reasons": reasons,
        "details": {
            "peak_ram_gb": peak_ram_gb,
            "max_ram_gb": max_ram_gb,
            "elapsed_time_h": current_time_h,
            "max_time_h": max_time_h
        }
    }
