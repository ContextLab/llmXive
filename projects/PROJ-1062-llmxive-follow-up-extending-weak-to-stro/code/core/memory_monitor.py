"""
Memory monitoring utility to track RAM usage and trigger batch size reduction.
"""
import os
import gc
import logging
from typing import Optional, Callable, Dict, Any

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logging.warning("psutil not installed. Memory monitoring will be limited.")

logger = logging.getLogger(__name__)

class MemoryMonitor:
    """
    Monitors system memory usage and provides OOM handling strategies.
    """
    def __init__(self, warning_threshold_gb: float = 6.5, hard_limit_gb: float = 7.0):
        self.warning_threshold_bytes = warning_threshold_gb * 1024**3
        self.hard_limit_bytes = hard_limit_gb * 1024**3
        self._current_batch_size: int = 1
        self._reduction_history: list = []

    def get_available_ram_gb(self) -> float:
        """Returns available RAM in GB."""
        if not HAS_PSUTIL:
            logger.warning("psutil unavailable. Returning -1.0 for RAM.")
            return -1.0
        mem = psutil.virtual_memory()
        return mem.available / (1024**3)

    def get_used_ram_gb(self) -> float:
        """Returns used RAM in GB."""
        if not HAS_PSUTIL:
            return -1.0
        mem = psutil.virtual_memory()
        return mem.used / (1024**3)

    def check_and_reduce(self, current_batch_size: int) -> int:
        """
        Checks memory usage. If above warning threshold, attempts to reduce batch size.
        Returns the new batch size (minimum 1).
        """
        used_gb = self.get_used_ram_gb()
        if used_gb < 0:
            return current_batch_size

        if used_gb > self.warning_threshold_bytes / (1024**3):
            logger.warning(f"Memory usage high ({used_gb:.2f} GB). Attempting batch size reduction.")
            new_size = max(1, current_batch_size - 1)
            if new_size < current_batch_size:
                self._reduction_history.append(new_size)
                gc.collect()
                logger.info(f"Reduced batch size to {new_size}")
            return new_size
        return current_batch_size

    def enforce_hard_floor(self, current_batch_size: int) -> int:
        """
        Enforces the hard floor of batch_size=1 if usage is critical.
        """
        used_gb = self.get_used_ram_gb()
        if used_gb > self.hard_limit_bytes / (1024**3):
            logger.critical(f"CRITICAL: Memory usage ({used_gb:.2f} GB) exceeds hard limit. Forcing batch_size=1.")
            gc.collect()
            return 1
        return current_batch_size
