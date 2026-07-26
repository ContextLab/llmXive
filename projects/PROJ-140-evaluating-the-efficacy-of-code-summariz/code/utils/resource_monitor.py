"""
CI Resource Monitor for FR-007 Compliance.

This module provides a context manager and standalone script to monitor
system resource usage (RAM and Runtime) during CI execution. It asserts
that usage stays within the limits defined in FR-007:
- Maximum RAM: 7 GB
- Maximum Runtime: 6 hours

Usage:
  1. As a context manager:
     with ResourceMonitor(limit_gb=7.0, limit_hours=6.0):
         # run heavy code
         pass

  2. As a CLI tool to check current usage or run a command:
     python code/utils/resource_monitor.py --check
     python code/utils/resource_monitor.py --command "python code/analysis/run_statistics.py"
"""

import os
import sys
import time
import subprocess
import resource
import signal
import psutil
from pathlib import Path
from typing import Optional, Callable, Any
from datetime import datetime

# Constants derived from FR-007
DEFAULT_LIMIT_GB = 7.0
DEFAULT_LIMIT_HOURS = 6.0
RAM_CHECK_INTERVAL = 1.0  # seconds

# Global state for the monitor
_monitor_start_time: Optional[float] = None
_monitor_pid: Optional[int] = None
_current_process: Optional[psutil.Process] = None
_max_rss_mb: float = 0.0
_is_monitoring: bool = False
_monitor_thread: Optional[Any] = None


def _get_memory_usage_mb() -> float:
    """
    Get the current resident set size (RSS) of the current process in MB.
    Uses psutil for cross-platform compatibility.
    """
    try:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except Exception:
        # Fallback to resource module if psutil fails (Unix only)
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # ru_maxrss is in KB on Linux, bytes on macOS (sometimes), usually KB on Unix
            # psutil is preferred, but this is a fallback
            return usage.ru_maxrss / 1024.0
        except Exception:
            return 0.0


def _monitor_loop(limit_gb: float, stop_event: Any):
    """
    Background thread loop to periodically check memory usage.
    """
    global _max_rss_mb, _is_monitoring

    while not stop_event.is_set():
        current_mb = _get_memory_usage_mb()
        if current_mb > _max_rss_mb:
            _max_rss_mb = current_mb

        limit_mb = limit_gb * 1024
        if current_mb > limit_mb * 0.9:  # Warn at 90%
            print(f"[ResourceMonitor] WARNING: Memory usage at {current_mb:.2f} MB "
                  f"({(current_mb / (limit_mb * 1024)) * 100:.1f}% of {limit_gb}GB limit).")

        time.sleep(RAM_CHECK_INTERVAL)
    _is_monitoring = False


class ResourceMonitor:
    """
    Context manager to monitor RAM and Runtime for CI compliance (FR-007).

    Asserts:
      - Memory usage does not exceed `limit_gb` (default 7.0 GB).
      - Runtime does not exceed `limit_hours` (default 6.0 hours).

    Raises:
      MemoryError: If RAM usage exceeds the limit.
      TimeoutError: If runtime exceeds the limit.
    """

    def __init__(self, limit_gb: float = DEFAULT_LIMIT_GB, limit_hours: float = DEFAULT_LIMIT_HOURS):
        self.limit_gb = limit_gb
        self.limit_hours = limit_hours
        self.limit_mb = limit_gb * 1024
        self.limit_seconds = limit_hours * 3600
        self.start_time: Optional[float] = None
        self.stop_event: Optional[Any] = None
        self.monitor_thread: Optional[Any] = None

    def __enter__(self):
        global _monitor_start_time, _max_rss_mb, _is_monitoring, _monitor_pid

        _max_rss_mb = 0.0
        self.start_time = time.time()
        _monitor_start_time = self.start_time
        _monitor_pid = os.getpid()
        _is_monitoring = True

        # Start background monitoring thread
        import threading
        self.stop_event = threading.Event()
        self.monitor_thread = threading.Thread(
            target=_monitor_loop,
            args=(self.limit_gb, self.stop_event),
            daemon=True
        )
        self.monitor_thread.start()

        # Set up signal handlers for graceful exit on timeout
        def timeout_handler(signum, frame):
            raise TimeoutError(
                f"CI Runtime Exceeded: Process ran for {time.time() - self.start_time:.2f} seconds "
                f"(Limit: {self.limit_hours} hours)."
            )

        # Only set alarm if on Unix (Windows doesn't support signal.SIGALRM)
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(self.limit_seconds))

        print(f"[ResourceMonitor] Started. Limit: {self.limit_gb}GB RAM, {self.limit_hours}h Runtime.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _is_monitoring

        if self.monitor_thread:
            self.stop_event.set()
            self.monitor_thread.join(timeout=2.0)

        # Cancel alarm if set
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)

        elapsed_time = time.time() - self.start_time if self.start_time else 0
        elapsed_hours = elapsed_time / 3600

        # Final Checks
        if exc_type is None:  # Only check if no exception already raised
            # Check Runtime
            if elapsed_time > self.limit_seconds:
                raise TimeoutError(
                    f"CI Runtime Exceeded: Process ran for {elapsed_hours:.2f} hours "
                    f"(Limit: {self.limit_hours} hours)."
                )

            # Check Memory (Final snapshot)
            current_mb = _get_memory_usage_mb()
            if current_mb > self.limit_mb:
                raise MemoryError(
                    f"CI Memory Exceeded: Peak usage was {_max_rss_mb:.2f} MB "
                    f"(Limit: {self.limit_mb:.2f} MB / {self.limit_gb} GB)."
                )

        print(f"[ResourceMonitor] Finished. Runtime: {elapsed_hours:.2f}h, Peak RAM: {_max_rss_mb:.2f} MB.")
        return False  # Do not suppress exceptions


def check_resources(limit_gb: float = DEFAULT_LIMIT_GB, limit_hours: float = DEFAULT_LIMIT_HOURS) -> bool:
    """
    Perform a one-off check of current resources.
    Returns True if within limits, raises exception otherwise.
    """
    current_mb = _get_memory_usage_mb()
    limit_mb = limit_gb * 1024

    if current_mb > limit_mb:
        raise MemoryError(
            f"Current memory usage ({current_mb:.2f} MB) exceeds limit ({limit_mb:.2f} MB)."
        )

    print(f"Resource Check Passed: {current_mb:.2f} MB / {limit_mb:.2f} MB.")
    return True


def main():
    """
    CLI entry point for resource monitoring.
    Usage:
      python code/utils/resource_monitor.py --check
      python code/utils/resource_monitor.py --command "<command>"
    """
    import argparse

    parser = argparse.ArgumentParser(description="CI Resource Monitor for FR-007 Compliance")
    parser.add_argument("--check", action="store_true", help="Check current resource usage and exit.")
    parser.add_argument("--command", type=str, help="Run a command under resource monitoring.")
    parser.add_argument("--limit-gb", type=float, default=DEFAULT_LIMIT_GB, help=f"RAM limit in GB (default: {DEFAULT_LIMIT_GB})")
    parser.add_argument("--limit-hours", type=float, default=DEFAULT_LIMIT_HOURS, help=f"Time limit in hours (default: {DEFAULT_LIMIT_HOURS})")

    args = parser.parse_args()

    if args.check:
        try:
            check_resources(args.limit_gb, args.limit_hours)
            print("SUCCESS: Resources within limits.")
            sys.exit(0)
        except (MemoryError, TimeoutError) as e:
            print(f"FAILURE: {e}")
            sys.exit(1)

    if args.command:
        print(f"Running command with limits: {args.limit_gb}GB, {args.limit_hours}h")
        try:
            with ResourceMonitor(limit_gb=args.limit_gb, limit_hours=args.limit_hours):
                # Execute the command
                result = subprocess.run(args.command, shell=True)
                if result.returncode != 0:
                    print(f"Command failed with exit code {result.returncode}")
                    sys.exit(result.returncode)
        except MemoryError as e:
            print(f"CI FAILURE: {e}")
            sys.exit(1)
        except TimeoutError as e:
            print(f"CI FAILURE: {e}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()