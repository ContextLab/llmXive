"""
Resource monitoring module for A/B test audit pipeline.

Implements FR-009: Monitor CPU and memory usage, enforce limits.
"""
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from threading import Thread
from typing import Dict, Any, Optional

from code.src.utils.logger import get_default_logger, get_error_message


# Resource limits per FR-009
MAX_MEMORY_GB = 2.0
MAX_CPU_CORES = 2.0
MAX_RUNTIME_HOURS = 6.0


def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    try:
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    # VmRSS is in kB
                    memory_kb = int(line.split()[1])
                    return memory_kb / (1024 * 1024)  # Convert to GB
        return 0.0
    except Exception:
        return 0.0


def get_cpu_cores() -> float:
    """Get current CPU usage as fraction of available cores."""
    try:
        with open('/proc/stat', 'r') as f:
            line = f.readline()
            parts = line.split()
            # Sum all CPU time values
            total = sum(int(x) for x in parts[1:])
            idle = int(parts[4])
            usage = 1.0 - (idle / total) if total > 0 else 0.0
            return usage * os.cpu_count() or 1.0
    except Exception:
        return 1.0


class ResourceMonitor:
    """Monitor resource usage and write logs."""

    def __init__(self, output_path: Path, logger: Optional[Any] = None):
        self.output_path = output_path
        self.logger = logger or get_default_logger()
        self.peak_memory_gb = 0.0
        self.peak_cpu = 0.0
        self.start_time = time.time()
        self._running = False
        self._thread: Optional[Thread] = None

    def start(self):
        """Start monitoring in background thread."""
        self._running = True
        self.start_time = time.time()
        self._thread = Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop monitoring and write final log."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        self._write_log()

    def _monitor_loop(self):
        """Background monitoring loop."""
        while self._running:
            memory_gb = get_memory_usage_gb()
            cpu = get_cpu_cores()

            self.peak_memory_gb = max(self.peak_memory_gb, memory_gb)
            self.peak_cpu = max(self.peak_cpu, cpu)

            # Check limits
            if memory_gb > MAX_MEMORY_GB:
                self.logger.error(f"ERR-301: Memory limit exceeded: {memory_gb:.2f}GB > {MAX_MEMORY_GB}GB")
                self._write_log()
                raise MemoryError(f"Memory limit exceeded: {memory_gb:.2f}GB")

            if cpu > MAX_CPU_CORES:
                self.logger.warning(f"CPU usage high: {cpu:.2f} cores")

            time.sleep(1.0)  # Check every second

    def _write_log(self):
        """Write resource usage log."""
        try:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'peak_memory_gb': self.peak_memory_gb,
                'peak_cpu_cores': self.peak_cpu,
                'runtime_seconds': time.time() - self.start_time,
                'limits': {
                    'max_memory_gb': MAX_MEMORY_GB,
                    'max_cpu_cores': MAX_CPU_CORES,
                    'max_runtime_hours': MAX_RUNTIME_HOURS
                }
            }
            with open(self.output_path, 'w') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to write resource log: {e}")


def start_monitoring(output_path: Path) -> ResourceMonitor:
    """Start resource monitoring and return monitor instance."""
    monitor = ResourceMonitor(output_path)
    monitor.start()
    return monitor


def stop_monitoring(monitor: ResourceMonitor):
    """Stop resource monitoring."""
    monitor.stop()


def write_resource_log(output_path: Path, peak_memory_gb: float, peak_cpu: float, runtime_seconds: float) -> bool:
    """Write resource log directly (without monitoring thread)."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'peak_memory_gb': peak_memory_gb,
            'peak_cpu_cores': peak_cpu,
            'runtime_seconds': runtime_seconds,
            'limits': {
                'max_memory_gb': MAX_MEMORY_GB,
                'max_cpu_cores': MAX_CPU_CORES,
                'max_runtime_hours': MAX_RUNTIME_HOURS
            }
        }
        with open(output_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"ERR-302: Failed to write resource log: {e}")
        return False


def main():
    """Main entry point for standalone resource monitoring test."""
    import argparse

    parser = argparse.ArgumentParser(description='Test resource monitoring')
    parser.add_argument('--output', type=str, default='output/resource_log.json', help='Output log path')
    parser.add_argument('--duration', type=int, default=5, help='Monitoring duration in seconds')
    args = parser.parse_args()

    print(f"Starting resource monitoring for {args.duration} seconds...")
    monitor = start_monitoring(Path(args.output))

    time.sleep(args.duration)

    stop_monitoring(monitor)

    print(f"Resource log written to {args.output}")
    print(f"Peak memory: {monitor.peak_memory_gb:.2f}GB")
    print(f"Peak CPU: {monitor.peak_cpu:.2f} cores")


if __name__ == '__main__':
    main()