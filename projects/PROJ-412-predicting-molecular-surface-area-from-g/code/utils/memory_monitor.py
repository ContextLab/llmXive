"""
Memory profiling wrapper for training loops.

This module provides the MemoryMonitor class to track peak RAM usage per epoch
and trigger early exit if memory usage exceeds the configured limit.
"""

import os
import sys
import logging
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

# Try to import psutil, fallback to tracemalloc if not available
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    import tracemalloc

from .config import get_project_root, load_env_config
from .logging import get_logger

logger = get_logger(__name__)


class MemoryMonitor:
    """
    Monitors memory usage during training epochs.

    Tracks peak RAM usage per epoch and triggers an early exit with a diagnostic
    report if memory usage exceeds MAX_RAM_GB from config.

    Attributes:
        max_ram_gb (float): Maximum allowed RAM usage in GB.
        peak_memory_per_epoch (List[float]): List of peak memory values (GB) per epoch.
        diagnostics (Dict[str, Any]): Diagnostic information for the final report.
        _start_time (Optional[float]): Start time of monitoring.
        _epoch_start_time (Optional[float]): Start time of current epoch.
        _tracemalloc_started (bool): Whether tracemalloc has been started.
    """

    def __init__(self, max_ram_gb: Optional[float] = None):
        """
        Initialize the MemoryMonitor.

        Args:
            max_ram_gb: Maximum RAM limit in GB. If None, loads from config.py.
        """
        # Load config
        config = load_env_config()
        self.max_ram_gb = max_ram_gb if max_ram_gb is not None else config.get('MAX_RAM_GB', 7.0)
        
        self.peak_memory_per_epoch: List[float] = []
        self.diagnostics: Dict[str, Any] = {
            'max_ram_gb': self.max_ram_gb,
            'exceeded': False,
            'exceeded_at_epoch': None,
            'peak_memory_gb': None,
            'timestamp': None
        }
        
        self._start_time: Optional[float] = None
        self._epoch_start_time: Optional[float] = None
        self._tracemalloc_started = False

        if HAS_PSUTIL:
            logger.info("MemoryMonitor: Using psutil for memory monitoring.")
        else:
            logger.warning("MemoryMonitor: psutil not found. Falling back to tracemalloc.")
            tracemalloc.start()
            self._tracemalloc_started = True

    def start(self) -> None:
        """Start the memory monitoring session."""
        self._start_time = time.time()
        self.peak_memory_per_epoch = []
        self.diagnostics = {
            'max_ram_gb': self.max_ram_gb,
            'exceeded': False,
            'exceeded_at_epoch': None,
            'peak_memory_gb': None,
            'timestamp': None
        }
        logger.info(f"MemoryMonitor started. Max RAM limit: {self.max_ram_gb} GB.")

    def _get_current_memory_gb(self) -> float:
        """
        Get current memory usage in GB.

        Returns:
            float: Current memory usage in GB.
        """
        if HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            memory_bytes = process.memory_info().rss
            return memory_bytes / (1024 ** 3)
        else:
            current, _ = tracemalloc.get_traced_memory()
            return current / (1024 ** 3)

    def start_epoch(self) -> None:
        """Record the start of a new epoch."""
        self._epoch_start_time = time.time()

    def end_epoch(self, epoch: int) -> bool:
        """
        Record the end of an epoch and check memory limits.

        Args:
            epoch: The current epoch number (1-indexed).

        Returns:
            bool: True if memory limit was exceeded, False otherwise.
        """
        if self._epoch_start_time is None:
            logger.warning("MemoryMonitor: end_epoch called without start_epoch.")
            return False

        current_memory_gb = self._get_current_memory_gb()
        self.peak_memory_per_epoch.append(current_memory_gb)

        exceeded = current_memory_gb > self.max_ram_gb

        if exceeded:
            self.diagnostics['exceeded'] = True
            self.diagnostics['exceeded_at_epoch'] = epoch
            self.diagnostics['peak_memory_gb'] = current_memory_gb
            self.diagnostics['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            logger.error(
                f"MemoryMonitor: CRITICAL - Memory limit exceeded at epoch {epoch}! "
                f"Current usage: {current_memory_gb:.2f} GB (limit: {self.max_ram_gb} GB)."
            )
            self._generate_diagnostic_report()
            return True
        else:
            logger.info(
                f"Epoch {epoch}: Peak memory usage = {current_memory_gb:.2f} GB "
                f"(limit: {self.max_ram_gb} GB)"
            )
            return False

    def _generate_diagnostic_report(self) -> None:
        """Generate and save a diagnostic report when memory limit is exceeded."""
        project_root = get_project_root()
        logs_dir = project_root / 'logs'
        logs_dir.mkdir(parents=True, exist_ok=True)

        report_path = logs_dir / 'memory_exceeded_report.json'

        report_data = {
            'config': {
                'max_ram_gb': self.max_ram_gb,
                'total_epochs_monitored': len(self.peak_memory_per_epoch)
            },
            'memory_history_gb': self.peak_memory_per_epoch,
            'peak_memory_gb': max(self.peak_memory_per_epoch) if self.peak_memory_per_epoch else 0,
            'exceeded_at_epoch': self.diagnostics['exceeded_at_epoch'],
            'exceeded_memory_gb': self.diagnostics['peak_memory_gb'],
            'timestamp': self.diagnostics['timestamp'],
            'recommendation': (
                "Reduce batch size, use gradient accumulation, "
                "or increase available memory."
            )
        }

        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)

        logger.error(f"Diagnostic report saved to: {report_path}")

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of memory usage.

        Returns:
            Dict containing summary statistics.
        """
        if not self.peak_memory_per_epoch:
            return {'status': 'no_data', 'message': 'No epochs monitored yet.'}

        return {
            'total_epochs': len(self.peak_memory_per_epoch),
            'peak_memory_gb': max(self.peak_memory_per_epoch),
            'average_memory_gb': sum(self.peak_memory_per_epoch) / len(self.peak_memory_per_epoch),
            'min_memory_gb': min(self.peak_memory_per_epoch),
            'max_ram_limit_gb': self.max_ram_gb,
            'exceeded_limit': self.diagnostics['exceeded'],
            'exceeded_at_epoch': self.diagnostics['exceeded_at_epoch']
        }

    def stop(self) -> None:
        """Stop the memory monitoring session."""
        if self._tracemalloc_started:
            tracemalloc.stop()
            self._tracemalloc_started = False

        summary = self.get_summary()
        logger.info(f"MemoryMonitor stopped. Summary: {summary}")

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        if exc_type is not None:
            logger.error(f"MemoryMonitor: Exception occurred: {exc_type.__name__}: {exc_val}")
        return False