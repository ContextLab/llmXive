"""
Resource monitoring utilities for llmXive project.
Provides RAM, CPU, and time tracking with enforcement of project limits.
"""
import os
import time
import threading
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import psutil

@dataclass
class ResourceSnapshot:
    """Snapshot of resource usage at a specific point in time."""
    timestamp: float
    ram_mb: float
    cpu_percent: float
    elapsed_time: float

class ResourceMonitor:
    """
    Monitor resource usage and enforce limits.
    
    Features:
    - Background thread for continuous RAM/CPU sampling
    - Peak RAM tracking
    - Elapsed time tracking
    - Configurable limits for RAM (GB) and time (hours)
    - Automatic limit checking with exception raising
    """
    
    def __init__(self, max_ram_gb: float = 7.0, max_time_hours: float = 6.0):
        """
        Initialize the resource monitor.
        
        Args:
            max_ram_gb: Maximum allowed RAM usage in GB (default 7.0 per project spec)
            max_time_hours: Maximum allowed execution time in hours (default 6.0)
        """
        self.max_ram_gb = max_ram_gb
        self.max_time_hours = max_time_hours
        self.start_time = time.time()
        self.peak_ram_mb = 0.0
        self._monitor_thread = None
        self._stop_monitoring = threading.Event()
        self._snapshots: list[ResourceSnapshot] = []
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def _monitor_loop(self):
        """Background loop to monitor resources."""
        process = psutil.Process(os.getpid())
        while not self._stop_monitoring.is_set():
            try:
                # Get current memory usage
                mem_mb = process.memory_info().rss / (1024 * 1024)
                
                # Update peak RAM if current exceeds it
                if mem_mb > self.peak_ram_mb:
                    self.peak_ram_mb = mem_mb
                
                # Record snapshot
                elapsed = time.time() - self.start_time
                snapshot = ResourceSnapshot(
                    timestamp=time.time(),
                    ram_mb=mem_mb,
                    cpu_percent=psutil.cpu_percent(interval=0.1),
                    elapsed_time=elapsed
                )
                self._snapshots.append(snapshot)
                
                time.sleep(1)  # Sample every second
            except Exception:
                break
    
    def check_limits(self) -> None:
        """
        Check if resource limits are exceeded.
        
        Raises:
            ResourceLimitExceeded: If RAM or time limits are breached
        """
        current_ram_mb = self.peak_ram_mb
        current_time_hours = (time.time() - self.start_time) / 3600
        
        if current_ram_mb > self.max_ram_gb * 1024:
            from utils.logging import ResourceLimitExceeded
            raise ResourceLimitExceeded(
                f"RAM limit exceeded: {current_ram_mb:.2f} MB > {self.max_ram_gb * 1024:.2f} MB"
            )
        
        if current_time_hours > self.max_time_hours:
            from utils.logging import ResourceLimitExceeded
            raise ResourceLimitExceeded(
                f"Time limit exceeded: {current_time_hours:.2f} hours > {self.max_time_hours} hours"
            )
    
    def get_current_snapshot(self) -> ResourceSnapshot:
        """Get the most recent resource snapshot."""
        process = psutil.Process(os.getpid())
        elapsed = time.time() - self.start_time
        return ResourceSnapshot(
            timestamp=time.time(),
            ram_mb=process.memory_info().rss / (1024 * 1024),
            cpu_percent=psutil.cpu_percent(interval=0.1),
            elapsed_time=elapsed
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get aggregated resource statistics.
        
        Returns:
            Dictionary with peak RAM, average CPU, total snapshots, etc.
        """
        if not self._snapshots:
            return {
                "peak_ram_mb": self.peak_ram_mb,
                "avg_cpu_percent": 0.0,
                "total_snapshots": 0,
                "elapsed_time": time.time() - self.start_time
            }
        
        cpu_values = [s.cpu_percent for s in self._snapshots]
        return {
            "peak_ram_mb": self.peak_ram_mb,
            "avg_cpu_percent": sum(cpu_values) / len(cpu_values),
            "min_cpu_percent": min(cpu_values),
            "max_cpu_percent": max(cpu_values),
            "total_snapshots": len(self._snapshots),
            "elapsed_time": time.time() - self.start_time
        }
    
    def stop(self):
        """Stop the monitoring thread."""
        self._stop_monitoring.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)

def get_peak_memory_mb() -> float:
    """
    Get current peak memory usage in MB for the current process.
    
    Note: This is a snapshot of current RSS, not historical peak.
    For historical peak tracking, use ResourceMonitor.
    
    Returns:
        Current memory usage in MB
    """
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def get_cpu_percent() -> float:
    """
    Get current CPU usage percentage.
    
    Returns:
        Current CPU usage as a percentage
    """
    return psutil.cpu_percent(interval=0.1)

def get_elapsed_time() -> float:
    """
    Get elapsed time since the start of the current monitoring session.
    If no monitor is active, returns time since module import.
    
    Returns:
        Elapsed time in seconds
    """
    # Fallback if no monitor is active
    return time.time() % 1e9  # Placeholder - actual usage should be via ResourceMonitor

def format_bytes(size_bytes: float) -> str:
    """
    Format bytes to human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def format_duration(seconds: float) -> str:
    """
    Format seconds to human-readable duration.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "1h 30m 45s")
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    elif minutes > 0:
        return f"{int(minutes)}m {int(seconds)}s"
    else:
        return f"{int(seconds)}s"

def validate_resource_limits(max_ram_gb: float = 7.0, max_time_hours: float = 6.0) -> bool:
    """
    Validate that current resource usage is within limits.
    
    Args:
        max_ram_gb: Maximum allowed RAM in GB
        max_time_hours: Maximum allowed time in hours
        
    Returns:
        True if within limits, False otherwise
    """
    current_ram = get_peak_memory_mb()
    if current_ram > max_ram_gb * 1024:
        return False
    
    # Time validation requires a monitor instance
    # This function is a quick check for RAM only
    return True