import os
import time
import psutil
import logging
from typing import Optional, List, Callable
from dataclasses import dataclass

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Default memory threshold in GB (matching project constraints)
DEFAULT_MEMORY_THRESHOLD_GB = 14.0

@dataclass
class MemorySnapshot:
    timestamp: float
    ram_used_gb: float
    ram_available_gb: float
    ram_percent: float
    action_taken: Optional[str] = None

class MemoryMonitor:
    """
    Monitors runtime memory usage and enforces safety constraints.
    If RAM usage approaches a high threshold, it triggers dynamic
    batch size reduction or pauses execution.
    """

    def __init__(
        self,
        threshold_gb: float = DEFAULT_MEMORY_THRESHOLD_GB,
        warning_threshold_ratio: float = 0.85,
        critical_threshold_ratio: float = 0.95
    ):
        self.threshold_gb = threshold_gb
        self.warning_threshold_ratio = warning_threshold_ratio
        self.critical_threshold_ratio = critical_threshold_ratio
        self.snapshots: List[MemorySnapshot] = []
        self._process = psutil.Process(os.getpid())

    def get_current_memory_gb(self) -> float:
        """Returns current RAM usage in GB."""
        mem_info = self._process.memory_info()
        return mem_info.rss / (1024 ** 3)

    def get_available_memory_gb(self) -> float:
        """Returns available system RAM in GB."""
        mem_info = psutil.virtual_memory()
        return mem_info.available / (1024 ** 3)

    def check_memory_constraint(self) -> bool:
        """
        Checks if current memory usage exceeds the configured threshold.
        Returns True if safe to continue, False if constraint violated.
        """
        current_gb = self.get_current_memory_gb()
        return current_gb < self.threshold_gb

    def monitor_and_adjust(
        self,
        current_batch_size: int,
        reduce_callback: Callable[[int], int],
        pause_callback: Optional[Callable[[], None]] = None
    ) -> int:
        """
        Monitors memory and adjusts batch size or pauses if necessary.

        Args:
            current_batch_size: The current batch size being used.
            reduce_callback: A function that takes the current batch size
                             and returns a reduced batch size.
            pause_callback: Optional function to pause execution (e.g., gc.collect()).

        Returns:
            The new batch size (possibly reduced).
        """
        current_gb = self.get_current_memory_gb()
        available_gb = self.get_available_memory_gb()
        total_gb = psutil.virtual_memory().total / (1024 ** 3)
        percent_used = (current_gb / total_gb) * 100 if total_gb > 0 else 0

        action = None
        new_batch_size = current_batch_size

        # Log snapshot
        snapshot = MemorySnapshot(
            timestamp=time.time(),
            ram_used_gb=current_gb,
            ram_available_gb=available_gb,
            ram_percent=percent_used
        )

        if percent_used >= self.critical_threshold_ratio * 100:
            action = "CRITICAL: Memory threshold exceeded. Pausing and reducing batch size."
            logger.warning(action)
            if pause_callback:
                pause_callback()
            new_batch_size = reduce_callback(current_batch_size)
            snapshot.action_taken = f"Reduced batch to {new_batch_size}"

        elif percent_used >= self.warning_threshold_ratio * 100:
            action = "WARNING: Memory usage high. Reducing batch size preemptively."
            logger.warning(action)
            new_batch_size = reduce_callback(current_batch_size)
            snapshot.action_taken = f"Reduced batch to {new_batch_size}"

        else:
            snapshot.action_taken = "OK"

        self.snapshots.append(snapshot)
        return new_batch_size

    def log_summary(self):
        """Logs a summary of memory monitoring events."""
        if not self.snapshots:
            return

        critical_count = sum(1 for s in self.snapshots if "CRITICAL" in (s.action_taken or ""))
        warning_count = sum(1 for s in self.snapshots if "WARNING" in (s.action_taken or ""))
        logger.info(
            f"Memory Monitor Summary: {len(self.snapshots)} samples, "
            f"{critical_count} critical events, {warning_count} warning events."
        )
