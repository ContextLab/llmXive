"""
Memory profiling wrapper for the molecular surface area prediction pipeline.

This module provides the MemoryMonitor class to track RAM usage during training
and trigger early exit if limits are exceeded.
"""
import os
import sys
import logging
import time
import json
import tracemalloc
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Import configuration
from code.config import MAX_RAM_GB, PROJECT_ROOT, LOGS_DIR
from code.utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)


class MemoryMonitor:
    """
    A context manager and utility class for monitoring peak RAM usage.

    This class tracks memory consumption per epoch, logs diagnostics, and
    triggers an early exit if the configured MAX_RAM_GB limit is exceeded.

    Attributes:
        max_ram_gb (float): Maximum allowed RAM usage in GB.
        peak_memory_mb (float): Peak memory usage observed (in MB).
        current_memory_mb (float): Current memory usage (in MB).
        epoch_logs (List[Dict]): List of memory snapshots per epoch.
        start_time (float): Start time of monitoring.
        is_monitoring (bool): Flag indicating if monitoring is active.
    """

    def __init__(self, max_ram_gb: Optional[float] = None):
        """
        Initialize the MemoryMonitor.

        Args:
            max_ram_gb: Maximum RAM limit in GB. If None, uses config.MAX_RAM_GB.
        """
        self.max_ram_gb = max_ram_gb if max_ram_gb is not None else MAX_RAM_GB
        self.peak_memory_mb = 0.0
        self.current_memory_mb = 0.0
        self.epoch_logs: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None
        self.is_monitoring = False
        self._tracemalloc_started = False

        # Ensure log directory exists
        os.makedirs(LOGS_DIR, exist_ok=True)

    def start(self) -> None:
        """Start memory monitoring using tracemalloc."""
        if self.is_monitoring:
            logger.warning("MemoryMonitor is already running.")
            return

        logger.info("Starting memory monitoring...")
        tracemalloc.start()
        self.start_time = time.time()
        self.is_monitoring = True
        self._tracemalloc_started = True
        self.peak_memory_mb = 0.0

    def stop(self) -> None:
        """Stop memory monitoring."""
        if not self.is_monitoring:
            logger.warning("MemoryMonitor is not running.")
            return

        self._update_current_memory()
        tracemalloc.stop()
        self.is_monitoring = False
        self._tracemalloc_started = False
        logger.info("Memory monitoring stopped.")

    def _update_current_memory(self) -> None:
        """Update current and peak memory usage."""
        if not self._tracemalloc_started:
            return

        current, peak = tracemalloc.get_traced_memory()
        self.current_memory_mb = current / (1024 * 1024)
        if self.current_memory_mb > self.peak_memory_mb:
            self.peak_memory_mb = self.current_memory_mb

    def check_limit(self) -> bool:
        """
        Check if current memory usage exceeds the limit.

        Returns:
            bool: True if limit is exceeded, False otherwise.
        """
        self._update_current_memory()
        limit_mb = self.max_ram_gb * 1024

        if self.current_memory_mb > limit_mb:
            logger.critical(
                f"Memory limit exceeded: {self.current_memory_mb:.2f} MB > "
                f"{limit_mb:.2f} MB ({self.max_ram_gb} GB)."
            )
            return True
        return False

    def log_epoch(self, epoch: int, loss: Optional[float] = None) -> None:
        """
        Log memory statistics for a specific epoch.

        Args:
            epoch: The epoch number.
            loss: Optional loss value for the epoch.
        """
        self._update_current_memory()
        timestamp = datetime.now().isoformat()

        log_entry = {
            "timestamp": timestamp,
            "epoch": epoch,
            "current_memory_mb": round(self.current_memory_mb, 2),
            "peak_memory_mb": round(self.peak_memory_mb, 2),
            "max_ram_gb": self.max_ram_gb,
            "limit_mb": round(self.max_ram_gb * 1024, 2),
            "exceeded": self.current_memory_mb > (self.max_ram_gb * 1024)
        }

        if loss is not None:
            log_entry["loss"] = round(loss, 4)

        self.epoch_logs.append(log_entry)
        logger.info(
            f"Epoch {epoch}: Current={self.current_memory_mb:.2f} MB, "
            f"Peak={self.peak_memory_mb:.2f} MB"
        )

    def generate_diagnostic_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate a diagnostic report of memory usage.

        Args:
            output_path: Path to save the JSON report. If None, uses default path.

        Returns:
            str: Path to the generated report.
        """
        self._update_current_memory()

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(
                LOGS_DIR, f"memory_report_{timestamp}.json"
            )

        report = {
            "summary": {
                "max_ram_gb": self.max_ram_gb,
                "peak_memory_mb": round(self.peak_memory_mb, 2),
                "current_memory_mb": round(self.current_memory_mb, 2),
                "limit_exceeded": self.peak_memory_mb > (self.max_ram_gb * 1024),
                "total_epochs_logged": len(self.epoch_logs)
            },
            "epoch_details": self.epoch_logs,
            "generated_at": datetime.now().isoformat()
        }

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Memory diagnostic report saved to: {output_path}")
        return output_path

    def __enter__(self) -> 'MemoryMonitor':
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()
        if exc_type is not None:
            logger.warning(f"Memory monitoring stopped due to exception: {exc_type}")
            # Generate report on exception
            self.generate_diagnostic_report()
        elif self.peak_memory_mb > (self.max_ram_gb * 1024):
            logger.warning("Peak memory exceeded limit during execution.")
            self.generate_diagnostic_report()


def get_memory_usage_mb() -> float:
    """
    Utility function to get current memory usage in MB.

    Returns:
        float: Current memory usage in MB.
    """
    try:
        import tracemalloc
        if tracemalloc.is_tracing():
            current, _ = tracemalloc.get_traced_memory()
            return current / (1024 * 1024)
        return 0.0
    except Exception:
        return 0.0

def check_memory_limit(max_ram_gb: Optional[float] = None) -> bool:
    """
    Utility function to check if current memory exceeds the limit.

    Args:
        max_ram_gb: Maximum RAM limit in GB. If None, uses config value.

    Returns:
        bool: True if limit exceeded, False otherwise.
    """
    monitor = MemoryMonitor(max_ram_gb)
    return monitor.check_limit()

def main() -> None:
    """
    Main function to demonstrate memory monitoring.
    """
    logger.info("Running MemoryMonitor demonstration...")

    monitor = MemoryMonitor()

    with monitor:
        # Simulate some memory usage
        data = []
        for i in range(100):
            data.append([j for j in range(10000)])
            monitor.log_epoch(i, loss=0.5 - (i * 0.001))

            # Check limit periodically
            if monitor.check_limit():
                logger.error("Memory limit reached during simulation.")
                monitor.generate_diagnostic_report()
                break

        # Final report
        report_path = monitor.generate_diagnostic_report()
        print(f"Report generated at: {report_path}")

if __name__ == "__main__":
    main()