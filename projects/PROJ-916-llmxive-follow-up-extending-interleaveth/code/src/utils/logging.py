"""
Logging infrastructure for tracking RAM usage and execution time per step.

This module provides utilities to monitor memory consumption via tracemalloc
and measure execution time for individual pipeline steps.
"""
import logging
import sys
import time
import tracemalloc
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

# Configure a default logger for the module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


@dataclass
class MemorySnapshot:
    """Snapshot of memory usage at a specific point in time."""
    timestamp: datetime
    step_name: str
    current_memory_mb: float
    peak_memory_mb: float
    step_duration_seconds: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to a dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "step_name": self.step_name,
            "current_memory_mb": self.current_memory_mb,
            "peak_memory_mb": self.peak_memory_mb,
            "step_duration_seconds": self.step_duration_seconds
        }


@dataclass
class StepTimer:
    """Context manager to track execution time of a specific step."""
    step_name: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration_seconds: Optional[float] = None

    def start(self) -> None:
        """Start the timer."""
        self.start_time = time.perf_counter()
        logger.info(f"Starting step: {self.step_name}")

    def stop(self) -> float:
        """Stop the timer and return the duration."""
        if self.start_time is None:
            raise RuntimeError("Timer has not been started. Call start() first.")
        self.end_time = time.perf_counter()
        self.duration_seconds = self.end_time - self.start_time
        logger.info(f"Completed step: {self.step_name} in {self.duration_seconds:.4f}s")
        return self.duration_seconds


class RAMTracker:
    """
    Tracks RAM usage over time using tracemalloc.

    This class manages the lifecycle of tracemalloc and provides methods
    to record snapshots of memory usage.
    """
    def __init__(self, log_level: int = logging.INFO):
        self.snapshots: List[MemorySnapshot] = []
        self.is_tracking = False
        self.log_level = log_level

    def start(self) -> None:
        """Start tracking memory allocations."""
        if not self.is_tracking:
            tracemalloc.start()
            self.is_tracking = True
            logger.info("tracemalloc started.")

    def stop(self) -> None:
        """Stop tracking memory allocations."""
        if self.is_tracking:
            tracemalloc.stop()
            self.is_tracking = False
            logger.info("tracemalloc stopped.")

    def get_current_memory_mb(self) -> float:
        """Get the current memory usage in MB."""
        if not self.is_tracking:
            # If not tracking, return 0 or raise an error depending on desired behavior
            # Returning 0 is safer for non-tracing environments, but we log a warning
            logger.warning("tracemalloc is not running. Returning 0.0 MB.")
            return 0.0
        current, peak = tracemalloc.get_traced_memory()
        return current / (1024 * 1024)

    def get_peak_memory_mb(self) -> float:
        """Get the peak memory usage since tracking started in MB."""
        if not self.is_tracking:
            logger.warning("tracemalloc is not running. Returning 0.0 MB.")
            return 0.0
        current, peak = tracemalloc.get_traced_memory()
        return peak / (1024 * 1024)

    def record_snapshot(self, step_name: str, duration_seconds: Optional[float] = None) -> MemorySnapshot:
        """
        Record a memory snapshot for a given step.

        Args:
            step_name: Name of the step being tracked.
            duration_seconds: Optional duration of the step.

        Returns:
            MemorySnapshot object containing the recorded data.
        """
        current_mem = self.get_current_memory_mb()
        peak_mem = self.get_peak_memory_mb()
        timestamp = datetime.now()

        snapshot = MemorySnapshot(
            timestamp=timestamp,
            step_name=step_name,
            current_memory_mb=current_mem,
            peak_memory_mb=peak_mem,
            step_duration_seconds=duration_seconds
        )
        self.snapshots.append(snapshot)
        logger.log(
            self.log_level,
            f"Snapshot [{step_name}]: Current={current_mem:.2f}MB, Peak={peak_mem:.2f}MB"
        )
        return snapshot

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all recorded snapshots.

        Returns:
            Dictionary containing summary statistics.
        """
        if not self.snapshots:
            return {
                "total_steps": 0,
                "max_current_memory_mb": 0.0,
                "max_peak_memory_mb": 0.0,
                "total_duration_seconds": 0.0
            }

        max_current = max(s.current_memory_mb for s in self.snapshots)
        max_peak = max(s.peak_memory_mb for s in self.snapshots)
        total_duration = sum(
            s.step_duration_seconds or 0.0 for s in self.snapshots
        )

        return {
            "total_steps": len(self.snapshots),
            "max_current_memory_mb": max_current,
            "max_peak_memory_mb": max_peak,
            "total_duration_seconds": total_duration
        }


@contextmanager
def track_step(step_name: str, ram_tracker: Optional[RAMTracker] = None):
    """
    Context manager to track both execution time and memory for a step.

    Args:
        step_name: Name of the step.
        ram_tracker: Optional RAMTracker instance. If None, a temporary one is created.
    """
    timer = StepTimer(step_name)
    tracker = ram_tracker if ram_tracker else RAMTracker()

    # Ensure tracking is started if we are using a tracker
    if not tracker.is_tracking:
        tracker.start()

    try:
        timer.start()
        yield timer
        timer.stop()
        # Record snapshot after the step completes
        tracker.record_snapshot(step_name, duration_seconds=timer.duration_seconds)
    finally:
        # If we created a temporary tracker, stop it here
        if ram_tracker is None:
            tracker.stop()


# Global instance for convenience if needed, though passing explicitly is preferred
_global_tracker: Optional[RAMTracker] = None

def start_tracing() -> RAMTracker:
    """
    Start the global RAM tracker.

    Returns:
        The global RAMTracker instance.
    """
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = RAMTracker()
    _global_tracker.start()
    logger.info("Global tracing started.")
    return _global_tracker

def stop_tracing() -> Optional[Dict[str, Any]]:
    """
    Stop the global RAM tracker and return summary.

    Returns:
        Summary dictionary or None if tracking wasn started.
    """
    global _global_tracker
    if _global_tracker is None or not _global_tracker.is_tracking:
        logger.warning("Global tracing was not active.")
        return None

    summary = _global_tracker.get_summary()
    _global_tracker.stop()
    logger.info(f"Global tracing stopped. Summary: {summary}")
    return summary