"""
Memory monitoring utility for llmXive project.
Verifies memory usage stays within acceptable limits during execution.
"""
import os
import sys
import time
import json
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not installed. Memory monitoring will be limited.")

from utils.config import get_project_root, get_hyperparameter


@dataclass
class MemorySnapshot:
    """Represents a single memory usage snapshot."""
    timestamp: str
    process_memory_mb: float
    system_memory_percent: float
    system_memory_available_mb: float
    peak_memory_mb: float = 0.0


class MemoryMonitor:
    """
    Monitors memory usage of the current process and system during execution.
    Provides real-time monitoring and generates a summary report.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the memory monitor.

        Args:
            project_root: Project root directory. If None, uses config.
        """
        self.project_root = project_root or get_project_root()
        self.samples: List[MemorySnapshot] = []
        self.peak_memory_mb: float = 0.0
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.check_interval: float = get_hyperparameter("memory_check_interval", default=1.0)
        self.max_memory_limit_mb: float = get_hyperparameter("max_memory_limit_mb", default=6000.0)

        # Ensure output directory exists
        self.log_dir = self.project_root / "data" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_process(self):
        """Get the current process object."""
        if PSUTIL_AVAILABLE:
            return psutil.Process(os.getpid())
        return None

    def _get_system_memory(self):
        """Get system memory information."""
        if PSUTIL_AVAILABLE:
            mem = psutil.virtual_memory()
            return {
                "percent": mem.percent,
                "available_mb": mem.available / (1024 * 1024),
                "total_mb": mem.total / (1024 * 1024)
            }
        return {"percent": 0.0, "available_mb": 0.0, "total_mb": 0.0}

    def _get_process_memory_mb(self):
        """Get current process memory usage in MB."""
        process = self._get_process()
        if process:
            # RSS (Resident Set Size) is the actual physical memory used
            return process.memory_info().rss / (1024 * 1024)
        return 0.0

    def _take_snapshot(self) -> MemorySnapshot:
        """Take a single memory snapshot."""
        process_mem = self._get_process_memory_mb()
        system_mem = self._get_system_memory()

        # Update peak memory
        if process_mem > self.peak_memory_mb:
            self.peak_memory_mb = process_mem

        snapshot = MemorySnapshot(
            timestamp=datetime.now().isoformat(),
            process_memory_mb=round(process_mem, 2),
            system_memory_percent=round(system_mem["percent"], 2),
            system_memory_available_mb=round(system_mem["available_mb"], 2),
            peak_memory_mb=round(self.peak_memory_mb, 2)
        )
        self.samples.append(snapshot)
        return snapshot

    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.monitoring:
            try:
                snapshot = self._take_snapshot()
                # Log warning if approaching limit
                if snapshot.process_memory_mb > self.max_memory_limit_mb * 0.9:
                    print(f"⚠️  Memory warning: {snapshot.process_memory_mb:.2f} MB "
                          f"(limit: {self.max_memory_limit_mb:.0f} MB)")
            except Exception as e:
                print(f"Error during memory sampling: {e}")
            time.sleep(self.check_interval)

    def start(self):
        """Start background memory monitoring."""
        if self.monitoring:
            return

        self.monitoring = True
        self.samples = []
        self.peak_memory_mb = 0.0

        # Take initial snapshot
        self._take_snapshot()

        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print(f"✓ Memory monitoring started (interval: {self.check_interval}s, limit: {self.max_memory_limit_mb:.0f} MB)")

    def stop(self) -> Dict[str, Any]:
        """
        Stop monitoring and return summary statistics.

        Returns:
            Dictionary with memory statistics.
        """
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

        summary = self.get_summary()

        # Save report to file
        self._save_report(summary)

        print(f"✓ Memory monitoring stopped. Peak: {summary['peak_memory_mb']:.2f} MB")
        return summary

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics from collected samples.

        Returns:
            Dictionary with memory statistics.
        """
        if not self.samples:
            return {
                "status": "no_data",
                "message": "No memory samples collected"
            }

        process_mem_values = [s.process_memory_mb for s in self.samples]
        system_mem_values = [s.system_memory_percent for s in self.samples]

        summary = {
            "status": "success" if self.peak_memory_mb <= self.max_memory_limit_mb else "exceeded",
            "timestamp": datetime.now().isoformat(),
            "sample_count": len(self.samples),
            "duration_seconds": len(self.samples) * self.check_interval,
            "peak_memory_mb": round(self.peak_memory_mb, 2),
            "max_memory_limit_mb": self.max_memory_limit_mb,
            "within_limits": self.peak_memory_mb <= self.max_memory_limit_mb,
            "statistics": {
                "process_memory_mb": {
                    "min": round(min(process_mem_values), 2),
                    "max": round(max(process_mem_values), 2),
                    "mean": round(sum(process_mem_values) / len(process_mem_values), 2),
                    "median": round(sorted(process_mem_values)[len(process_mem_values)//2], 2)
                },
                "system_memory_percent": {
                    "min": round(min(system_mem_values), 2),
                    "max": round(max(system_mem_values), 2),
                    "mean": round(sum(system_mem_values) / len(system_mem_values), 2)
                }
            },
            "final_snapshot": asdict(self.samples[-1]) if self.samples else None
        }
        return summary

    def _save_report(self, summary: Dict[str, Any]):
        """Save memory monitoring report to file."""
        report_path = self.log_dir / "memory_monitor_report.json"
        with open(report_path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"✓ Memory report saved to: {report_path}")

    def check_limit(self) -> bool:
        """
        Check if current memory usage is within limits.

        Returns:
            True if within limits, False otherwise.
        """
        current_mem = self._get_process_memory_mb()
        return current_mem <= self.max_memory_limit_mb

    def get_current_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics."""
        return {
            "process_memory_mb": self._get_process_memory_mb(),
            "system_memory_percent": self._get_system_memory()["percent"],
            "peak_memory_mb": self.peak_memory_mb
        }


def verify_memory_limits(max_memory_mb: Optional[float] = None, check_interval: float = 1.0) -> Dict[str, Any]:
    """
    Convenience function to monitor memory usage for a duration and verify limits.

    Args:
        max_memory_mb: Maximum allowed memory in MB. If None, uses config.
        check_interval: Interval between checks in seconds.

    Returns:
        Summary dictionary with verification result.
    """
    monitor = MemoryMonitor()
    if max_memory_mb:
        monitor.max_memory_limit_mb = max_memory_mb
    monitor.check_interval = check_interval

    monitor.start()
    time.sleep(check_interval * 5)  # Monitor for at least 5 intervals
    summary = monitor.stop()

    return summary


def main():
    """Main entry point for standalone execution."""
    print("=" * 60)
    print("Memory Usage Verification Script")
    print("=" * 60)
    print()

    # Simulate some work to generate memory usage
    print("Starting memory monitoring...")
    print("Simulating workload (this will take ~10 seconds)...")
    print()

    monitor = MemoryMonitor()
    monitor.start()

    # Simulate some memory-intensive operations
    data_store = []
    for i in range(100):
        # Create some data to simulate memory usage
        chunk = [j * 2 for j in range(10000)]
        data_store.append(chunk)
        time.sleep(0.1)

        # Print periodic status
        if i % 10 == 0:
            current = monitor.get_current_usage()
            print(f"  Iteration {i+100}: Process memory = {current['process_memory_mb']:.2f} MB")

    # Clean up
    del data_store
    time.sleep(1)

    # Stop monitoring and get results
    summary = monitor.stop()

    print()
    print("=" * 60)
    print("Verification Results")
    print("=" * 60)
    print(f"Status: {summary['status'].upper()}")
    print(f"Peak Memory: {summary['peak_memory_mb']:.2f} MB")
    print(f"Memory Limit: {summary['max_memory_limit_mb']:.0f} MB")
    print(f"Within Limits: {'YES' if summary['within_limits'] else 'NO'}")
    print(f"Samples Collected: {summary['sample_count']}")
    print(f"Duration: {summary['duration_seconds']:.1f} seconds")
    print()

    if not summary['within_limits']:
        print("⚠️  WARNING: Memory limit exceeded!")
        sys.exit(1)
    else:
        print("✓ Memory usage within acceptable limits.")
        sys.exit(0)


if __name__ == "__main__":
    main()
