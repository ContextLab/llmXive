"""
Resource monitoring module for tracking CPU and memory usage.
Implements FR-009: Abort with ERR-301 when limits are exceeded.
Implements SC-008: Record peak CPU & memory to output/resource_log.json.
"""
import json
import logging
import os
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Import config for limits and seed
from code.src.config import get_config_summary
from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

# Resource limits per FR-009
MAX_RAM_GB = 2.0
MAX_CPU_CORES = 2.0
ERROR_CODE_RESOURCE_EXCEEDED = "ERR-301"

class ResourceMonitor:
    """Monitors CPU and memory usage in a background thread."""

    def __init__(self, logger: Optional[AuditLogger] = None):
        self.logger = logger or get_default_logger()
        self._stop_event = threading.Event()
        self._peak_memory_gb = 0.0
        self._peak_cpu_percent = 0.0
        self._monitor_thread: Optional[threading.Thread] = None
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None

    def _get_memory_usage_gb(self) -> float:
        """Get current memory usage in GB."""
        try:
            # Read from /proc/self/statm (Linux) or use resource module (Unix)
            # Fallback to psutil if available, else estimate
            import resource
            # ru_maxrss is in KB on Linux, convert to GB
            usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            usage_gb = usage_kb / (1024 * 1024)
            return usage_gb
        except (ImportError, AttributeError, OSError):
            # Fallback: try psutil if installed
            try:
                import psutil
                process = psutil.Process(os.getpid())
                return process.memory_info().rss / (1024 * 1024 * 1024)
            except ImportError:
                # If no method works, return 0 and log warning
                self.logger.warning("Could not determine memory usage; psutil not available and /proc not accessible")
                return 0.0

    def _get_cpu_percent(self) -> float:
        """Get current CPU usage percentage."""
        try:
            # Simple CPU usage estimation using time difference
            # For more accurate monitoring, psutil is preferred
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            # Fallback: estimate based on number of cores
            # This is less accurate but avoids hard dependency
            try:
                cpu_count = os.cpu_count() or 1
                # Estimate 100% if we can't measure
                return 100.0
            except Exception:
                return 0.0

    def _monitor_loop(self, interval: float = 1.0):
        """Background loop to monitor resources."""
        while not self._stop_event.is_set():
            try:
                mem_gb = self._get_memory_usage_gb()
                cpu_pct = self._get_cpu_percent()

                if mem_gb > self._peak_memory_gb:
                    self._peak_memory_gb = mem_gb
                if cpu_pct > self._peak_cpu_percent:
                    self._peak_cpu_percent = cpu_pct

                # Check limits and abort if exceeded
                if mem_gb > MAX_RAM_GB:
                    msg = get_error_message(ERROR_CODE_RESOURCE_EXCEEDED)
                    self.logger.error(f"{ERROR_CODE_RESOURCE_EXCEEDED}: Memory limit exceeded ({mem_gb:.2f}GB > {MAX_RAM_GB}GB)")
                    self._stop_event.set()
                    sys.exit(1)

                if cpu_pct > (MAX_CPU_CORES * 100):  # Convert cores to percentage
                    msg = get_error_message(ERROR_CODE_RESOURCE_EXCEEDED)
                    self.logger.error(f"{ERROR_CODE_RESOURCE_EXCEEDED}: CPU limit exceeded ({cpu_pct:.1f}% > {MAX_CPU_CORES * 100}%)" )
                    self._stop_event.set()
                    sys.exit(1)

            except Exception as e:
                self.logger.warning(f"Error during resource monitoring: {e}")

            self._stop_event.wait(interval)

    def start(self, interval: float = 1.0):
        """Start monitoring in a background thread."""
        self._start_time = datetime.utcnow()
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self._monitor_thread.start()

    def stop(self):
        """Stop monitoring and record end time."""
        self._end_time = datetime.utcnow()
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)

    def get_peak_usage(self) -> Dict[str, float]:
        """Return peak usage statistics."""
        return {
            "peak_memory_gb": round(self._peak_memory_gb, 4),
            "peak_cpu_percent": round(self._peak_cpu_percent, 2)
        }

    def get_duration_seconds(self) -> float:
        """Return monitoring duration in seconds."""
        if self._start_time and self._end_time:
            return (self._end_time - self._start_time).total_seconds()
        return 0.0

# Global monitor instance
_monitor: Optional[ResourceMonitor] = None

def start_monitoring(interval: float = 1.0) -> ResourceMonitor:
    """Start the global resource monitor."""
    global _monitor
    if _monitor is None:
        _monitor = ResourceMonitor()
    _monitor.start(interval)
    return _monitor

def stop_monitoring() -> Optional[ResourceMonitor]:
    """Stop the global resource monitor."""
    global _monitor
    if _monitor:
        _monitor.stop()
    return _monitor

def write_resource_log(output_path: str, monitor: Optional[ResourceMonitor] = None) -> Path:
    """Write resource usage log to JSON file."""
    if monitor is None:
        monitor = _monitor

    if monitor is None:
        raise RuntimeError("No resource monitor available. Call start_monitoring() first.")

    usage = monitor.get_peak_usage()
    duration = monitor.get_duration_seconds()

    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "duration_seconds": round(duration, 2),
        "peak_memory_gb": usage["peak_memory_gb"],
        "peak_cpu_percent": usage["peak_cpu_percent"],
        "limits": {
            "max_memory_gb": MAX_RAM_GB,
            "max_cpu_percent": MAX_CPU_CORES * 100
        },
        "within_limits": usage["peak_memory_gb"] <= MAX_RAM_GB and usage["peak_cpu_percent"] <= (MAX_CPU_CORES * 100)
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2)

    return path

def get_memory_usage_gb() -> float:
    """Convenience function to get current memory usage."""
    try:
        import resource
        usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return usage_kb / (1024 * 1024)
    except (ImportError, AttributeError, OSError):
        try:
            import psutil
            return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024 * 1024)
        except ImportError:
            return 0.0

def get_cpu_cores() -> float:
    """Get number of CPU cores available."""
    return float(os.cpu_count() or 1)

def main():
    """Main entry point for resource monitoring test."""
    logger = get_default_logger()
    logger.info("Starting resource monitor test...")

    monitor = start_monitoring(interval=0.5)

    # Simulate some work
    time.sleep(3)

    # Stop monitoring
    stop_monitoring()

    # Write log
    log_path = write_resource_log("output/resource_log.json", monitor)
    logger.info(f"Resource log written to {log_path}")

    # Verify limits
    usage = monitor.get_peak_usage()
    if usage["peak_memory_gb"] > MAX_RAM_GB:
        logger.error(f"{ERROR_CODE_RESOURCE_EXCEEDED}: Memory limit exceeded")
        sys.exit(1)
    if usage["peak_cpu_percent"] > (MAX_CPU_CORES * 100):
        logger.error(f"{ERROR_CODE_RESOURCE_EXCEEDED}: CPU limit exceeded")
        sys.exit(1)

    logger.info("Resource usage within limits")

if __name__ == "__main__":
    main()