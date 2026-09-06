import os
import sys
import time
import threading
from typing import Optional, Callable, Any
from pathlib import Path
import torch

class MemoryLimitExceeded(Exception):
    """Exception raised when memory limit is exceeded."""
    pass

def get_current_rss_kb() -> int:
    """Get current RSS memory usage in KB from /proc/self/status."""
    try:
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    # VmRSS:    12345 kB
                    parts = line.split()
                    return int(parts[1])
    except (FileNotFoundError, IOError, ValueError):
        # Fallback for non-Linux systems
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # ru_maxrss is in KB on Linux, bytes on macOS
            if sys.platform == 'darwin':
                return usage.ru_maxrss // 1024
            return usage.ru_maxrss
        except ImportError:
            return 0

def get_peak_rss_kb() -> int:
    """Get peak RSS memory usage in KB."""
    try:
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmPeak:'):
                    parts = line.split()
                    return int(parts[1])
    except (FileNotFoundError, IOError, ValueError):
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            if sys.platform == 'darwin':
                return usage.ru_maxrss // 1024
            return usage.ru_maxrss
        except ImportError:
            return 0

def get_peak_rss() -> int:
    """Get peak RSS in bytes (for compatibility)."""
    return get_peak_rss_kb() * 1024

class MemoryMonitor:
    """Monitor memory usage and enforce limits."""
    
    def __init__(self, limit_kb: int, checkpoint_dir: str):
        self.limit_kb = limit_kb
        self.checkpoint_dir = Path(checkpoint_dir)
        self.peak_rss_kb = 0
        self._monitoring = False
        self._monitor_thread = None
        
        # Ensure checkpoint directory exists
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def get_current_rss_kb(self) -> int:
        """Get current memory usage."""
        current = get_current_rss_kb()
        if current > self.peak_rss_kb:
            self.peak_rss_kb = current
        return current

    def check_limit(self) -> bool:
        """Check if current memory is within limit."""
        current = self.get_current_rss_kb()
        return current <= self.limit_kb

    def enforce(self, checkpoint_callback: Optional[Callable] = None) -> None:
        """Enforce memory limit, saving checkpoint if exceeded."""
        current = self.get_current_rss_kb()
        
        if current > self.limit_kb:
            if checkpoint_callback:
                checkpoint_callback(reason="oom_abort")
            raise MemoryLimitExceeded(
                f"Memory limit exceeded: {current / 1024:.1f}MB > {self.limit_kb / 1024:.1f}MB"
            )

    def start_monitoring(self, interval: float = 1.0) -> None:
        """Start background monitoring thread."""
        self._monitoring = True
        
        def monitor_loop():
            while self._monitoring:
                self.get_current_rss_kb()
                time.sleep(interval)
        
        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2.0)

def enforce_memory_limit(limit_kb: int, checkpoint_dir: str, checkpoint_callback: Optional[Callable] = None) -> None:
    """Standalone function to enforce memory limit."""
    monitor = MemoryMonitor(limit_kb, checkpoint_dir)
    monitor.enforce(checkpoint_callback)

class MemoryLimitEnforcer:
    """Context manager for memory-limited operations."""
    
    def __init__(self, limit_kb: int, checkpoint_dir: str, checkpoint_callback: Optional[Callable] = None):
        self.limit_kb = limit_kb
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_callback = checkpoint_callback
        self.monitor = MemoryMonitor(limit_kb, checkpoint_dir)

    def __enter__(self):
        self.monitor.get_current_rss_kb()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is MemoryLimitExceeded:
            # Checkpoint already saved in enforce
            return False
        return False

    def check(self) -> None:
        """Check memory and raise if exceeded."""
        self.monitor.enforce(self.checkpoint_callback)

    def save_checkpoint(self, reason: str = "memory_limit") -> Path:
        """Save checkpoint at current state."""
        checkpoint_path = self.checkpoint_dir / f"checkpoint_memory_{reason}_{int(time.time())}.pt"
        # This would be called by the trainer with actual model state
        return checkpoint_path