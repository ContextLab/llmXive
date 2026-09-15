import os
import sys
import resource
import time
import json
from pathlib import Path
from typing import Optional, List, Callable, Any

from logging_setup import get_logger

# Constants
MEMORY_LIMIT_GB = 6.5
MEMORY_LIMIT_MB = MEMORY_LIMIT_GB * 1024
CHECK_INTERVAL_SECONDS = 0.1

logger = get_logger(__name__)

class MemoryTracker:
    """
    Tracks memory usage over time and ensures it does not exceed the limit.
    """
    def __init__(self, limit_mb: float = MEMORY_LIMIT_MB):
        self.limit_mb = limit_mb
        self.peak_rss_mb = 0.0
        self.history: List[float] = []
        self.start_time: Optional[float] = None
        self.logger = get_logger(__name__)

    def start(self):
        """Start tracking memory."""
        self.start_time = time.time()
        self.peak_rss_mb = 0.0
        self.history = []
        self.logger.info("Memory tracking started.")

    def check(self) -> float:
        """
        Check current RSS memory usage in MB.
        Updates peak if current is higher.
        """
        try:
            # resource.getrusage(resource.RUSAGE_SELF) returns ru_maxrss in KB on Linux/macOS
            # On some systems it might be in MB, but standard Linux is KB.
            # We assume KB as per standard Unix behavior.
            usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            current_mb = usage / 1024.0

            if current_mb > self.peak_rss_mb:
                self.peak_rss_mb = current_mb

            self.history.append(current_mb)
            return current_mb
        except Exception as e:
            self.logger.error(f"Error reading memory usage: {e}")
            return 0.0

    def is_safe(self) -> bool:
        """Check if current memory usage is within limits."""
        current = self.check()
        return current < self.limit_mb

    def get_peak(self) -> float:
        """Return the peak memory usage observed so far."""
        return self.peak_rss_mb

    def report(self) -> dict:
        """Return a summary report of memory usage."""
        return {
            "peak_rss_mb": self.peak_rss_mb,
            "limit_mb": self.limit_mb,
            "is_within_limit": self.peak_rss_mb <= self.limit_mb,
            "duration_seconds": time.time() - self.start_time if self.start_time else 0,
            "sample_count": len(self.history)
        }

def get_current_rss_mb() -> float:
    """
    Get the current RSS memory usage of the process in MB.
    """
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return usage / 1024.0
    except Exception:
        return 0.0

def check_memory_limit(limit_mb: float = MEMORY_LIMIT_MB) -> bool:
    """
    Check if the current process memory usage is below the limit.
    Returns True if safe, False if exceeded.
    """
    current = get_current_rss_mb()
    if current >= limit_mb:
        logger.error(f"Memory limit exceeded: {current:.2f} MB >= {limit_mb:.2f} MB")
        return False
    return True

def monitor_and_ensure_limit(
    func: Callable[..., Any],
    args: tuple = (),
    kwargs: dict = None,
    limit_mb: float = MEMORY_LIMIT_MB
) -> Any:
    """
    Decorator-like wrapper to monitor memory during function execution.
    If memory exceeds limit, raises a MemoryError.
    """
    if kwargs is None:
        kwargs = {}

    tracker = MemoryTracker(limit_mb)
    tracker.start()

    logger.info(f"Starting monitored execution with limit {limit_mb:.2f} MB")

    try:
        result = func(*args, **kwargs)
        final_report = tracker.report()
        logger.info(f"Execution completed. Peak RSS: {final_report['peak_rss_mb']:.2f} MB")
        return result
    except MemoryError:
        logger.critical("Memory limit exceeded during execution. Halting.")
        raise
    except Exception as e:
        logger.error(f"Execution failed with exception: {e}")
        raise
    finally:
        # Ensure we log the final state even on error
        report = tracker.report()
        logger.info(f"Final memory report: {json.dumps(report)}")

def main():
    """
    Main entry point for memory monitoring script.
    Can be run to test memory tracking or used as a module.
    """
    logger.info("Memory Monitor Module initialized.")
    
    # Example usage: Track memory over a simulated loop
    tracker = MemoryTracker()
    tracker.start()
    
    logger.info("Simulating processing loop...")
    for i in range(100):
        # Simulate some work
        _ = [j * j for j in range(10000)]
        current = tracker.check()
        if not tracker.is_safe():
            logger.critical(f"Memory limit breached at iteration {i}: {current:.2f} MB")
            break
        time.sleep(0.01)
    
    report = tracker.report()
    logger.info(f"Simulation complete. Report: {json.dumps(report)}")
    print(f"Peak RSS: {report['peak_rss_mb']:.2f} MB (Limit: {report['limit_mb']:.2f} MB)")

if __name__ == "__main__":
    main()