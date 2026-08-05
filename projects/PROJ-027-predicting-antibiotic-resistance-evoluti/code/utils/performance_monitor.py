import os
import sys
import time
import logging
import resource
import psutil
from pathlib import Path
from typing import Optional, Dict, Any

from .logging import get_logger
from .config import get_max_isolates

logger = get_logger(__name__)

class PerformanceMonitor:
    """
    Monitors resource usage and enforces the N=1000 isolate limit for CI runs.
    Ensures the pipeline completes within the 6-hour constraint.
    """

    def __init__(self, max_isolates: Optional[int] = None):
        self.max_isolates = max_isolates or get_max_isolates()
        self.start_time: Optional[float] = None
        self.start_memory: Optional[int] = None
        self.process = psutil.Process(os.getpid())

    def start(self):
        """Start monitoring."""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss
        logger.info(f"Performance monitor started. Max isolates limit: {self.max_isolates}")

    def check_isolate_count(self, count: int, context: str = ""):
        """
        Enforce the isolate limit. Raises an error if the count exceeds the limit.
        This is the primary enforcement mechanism for the CI constraint.
        """
        if count > self.max_isolates:
            error_msg = (
                f"CRITICAL: Isolate count ({count}) exceeds the configured limit ({self.max_isolates}). "
                f"Context: {context}. "
                "The pipeline must strictly enforce N=1000 for CI to meet the 6-hour constraint. "
                "Please ensure the data ingestion step correctly applies the MAX_ISOLATES limit."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.debug(f"Isolate count check passed: {count} <= {self.max_isolates} ({context})")

    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage statistics."""
        current = self.process.memory_info()
        return {
            "current_rss_mb": current.rss / (1024 * 1024),
            "start_rss_mb": (self.start_memory or 0) / (1024 * 1024),
            "delta_rss_mb": (current.rss - (self.start_memory or 0)) / (1024 * 1024),
            "percent": self.process.memory_percent()
        }

    def check_time_limit(self, limit_hours: float = 6.0):
        """
        Check if the elapsed time exceeds the limit.
        Raises a warning if approaching, error if exceeded.
        """
        elapsed_hours = self.get_elapsed_time() / 3600.0
        if elapsed_hours >= limit_hours:
            error_msg = (
                f"CRITICAL: Execution time ({elapsed_hours:.2f} hours) exceeded the {limit_hours}-hour limit."
            )
            logger.error(error_msg)
            raise TimeoutError(error_msg)
        elif elapsed_hours >= limit_hours * 0.9:
            logger.warning(f"Approaching time limit: {elapsed_hours:.2f} hours elapsed ({limit_hours * 100}%)")

    def stop(self):
        """Stop monitoring and log summary."""
        if self.start_time is None:
            return

        elapsed = self.get_elapsed_time()
        mem_stats = self.get_memory_usage()

        logger.info(f"Performance monitor stopped.")
        logger.info(f"  Elapsed time: {elapsed:.2f}s ({elapsed/60:.2f}m)")
        logger.info(f"  Memory Usage: Current={mem_stats['current_rss_mb']:.1f}MB, Delta={mem_stats['delta_rss_mb']:.1f}MB ({mem_stats['percent']:.1f}%)")

def enforce_isolate_limit(count: int, limit: Optional[int] = None):
    """
    Convenience function to check isolate count against the limit.
    Raises ValueError if limit is exceeded.
    """
    limit = limit or get_max_isolates()
    if count > limit:
        raise ValueError(f"Isolate count {count} exceeds limit {limit}")

def main():
    """
    CLI entry point for testing the performance monitor.
    Usage: python code/utils/performance_monitor.py --check-isolates 1001
    """
    import argparse
    parser = argparse.ArgumentParser(description="Performance Monitor CLI")
    parser.add_argument("--check-isolates", type=int, help="Check if this isolate count exceeds the limit")
    parser.add_argument("--limit", type=int, default=None, help="Override the isolate limit")
    args = parser.parse_args()

    monitor = PerformanceMonitor(max_isolates=args.limit)

    if args.check_isolates is not None:
        try:
            monitor.check_isolate_count(args.check_isolates, "CLI Test")
            print(f"SUCCESS: {args.check_isolates} isolates is within the limit.")
        except ValueError as e:
            print(f"FAILED: {e}")
            sys.exit(1)
    else:
        print("Usage: python code/utils/performance_monitor.py --check-isolates <count>")

if __name__ == "__main__":
    main()
