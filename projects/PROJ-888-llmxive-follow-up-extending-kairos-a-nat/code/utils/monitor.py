"""
Resource monitoring utilities for llmXive project.
"""
import os
import time
import threading
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import psutil

@dataclass
class ResourceSnapshot:
    """Snapshot of resource usage."""
    timestamp: float
    ram_mb: float
    cpu_percent: float
    elapsed_time: float

class ResourceMonitor:
    """Monitor resource usage and enforce limits."""
    
    def __init__(self, max_ram_gb: float = 7.0, max_time_hours: float = 6.0):
        self.max_ram_gb = max_ram_gb
        self.max_time_hours = max_time_hours
        self.start_time = time.time()
        self.peak_ram_mb = 0.0
        self._monitor_thread = None
        self._stop_monitoring = threading.Event()
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def _monitor_loop(self):
        """Background loop to monitor resources."""
        process = psutil.Process(os.getpid())
        while not self._stop_monitoring.is_set():
            try:
                mem_mb = process.memory_info().rss / (1024 * 1024)
                if mem_mb > self.peak_ram_mb:
                    self.peak_ram_mb = mem_mb
                time.sleep(1)
            except Exception:
                break
    
    def check_limits(self) -> None:
        """Check if resource limits are exceeded."""
        current_ram_mb = self.peak_ram_mb
        current_time_hours = (time.time() - self.start_time) / 3600
        
        if current_ram_mb > self.max_ram_gb * 1024:
            from utils.logging import ResourceLimitExceeded
            raise ResourceLimitExceeded(f"RAM limit exceeded: {current_ram_mb:.2f} MB > {self.max_ram_gb * 1024:.2f} MB")
        
        if current_time_hours > self.max_time_hours:
            from utils.logging import ResourceLimitExceeded
            raise ResourceLimitExceeded(f"Time limit exceeded: {current_time_hours:.2f} hours > {self.max_time_hours} hours")
    
    def stop(self):
        """Stop the monitoring thread."""
        self._stop_monitoring.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)

def get_peak_memory_mb() -> float:
    """Get peak memory usage in MB."""
    process = psutil.Process(os.getpid())
    # psutil does not track peak RSS directly, we approximate with max RSS
    # For a more accurate peak, we'd need to track it manually or use /proc on Linux
    return process.memory_info().rss / (1024 * 1024)

def get_cpu_percent() -> float:
    """Get current CPU usage percentage."""
    return psutil.cpu_percent(interval=0.1)

def get_elapsed_time() -> float:
    """Get elapsed time since script start (approximate)."""
    # This is a placeholder; actual implementation would need a global start time
    return 0.0

def format_bytes(size_bytes: float) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def format_duration(seconds: float) -> str:
    """Format seconds to human-readable duration."""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    elif minutes > 0:
        return f"{int(minutes)}m {int(seconds)}s"
    else:
        return f"{int(seconds)}s"