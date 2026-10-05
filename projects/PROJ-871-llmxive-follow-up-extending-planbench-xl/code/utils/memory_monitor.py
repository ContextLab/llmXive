import os
import sys
import time
import json
import threading
from pathlib import Path
from typing import Optional, Dict, Any

class MemorySnapshot:
    """Represents a memory snapshot."""
    def __init__(self, timestamp: float, memory_mb: float):
        self.timestamp = timestamp
        self.memory_mb = memory_mb

class MemoryMonitor:
    """Monitors memory usage."""
    def __init__(self, interval: float = 1.0):
        self.interval = interval
        self.snapshots: list = []
        self._stop_event = threading.Event()
        self._thread = None
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while not self._stop_event.is_set():
            try:
                import psutil
                process = psutil.Process(os.getpid())
                memory_info = process.memory_info()
                snapshot = MemorySnapshot(
                    time.time(),
                    memory_info.rss / (1024 * 1024)  # Convert to MB
                )
                self.snapshots.append(snapshot)
            except ImportError:
                # psutil not available, skip
                pass
            except Exception:
                pass
            
            self._stop_event.wait(self.interval)
    
    def start(self):
        """Start monitoring."""
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop monitoring."""
        self._stop_event.set()
        if self._thread:
            self._thread.join()
    
    def get_peak_memory_mb(self) -> float:
        """Get peak memory usage in MB."""
        if not self.snapshots:
            return 0.0
        return max(s.memory_mb for s in self.snapshots)
    
    def get_log_path(self) -> Path:
        """Get the path for the memory log."""
        return Path('data/logs/memory_usage.jsonl')

def verify_memory_limits(peak_memory_mb: float, limit_gb: float = 7.0) -> Dict[str, Any]:
    """Verify memory usage against limits."""
    limit_mb = limit_gb * 1024
    within_limit = peak_memory_mb <= limit_mb
    
    return {
        'peak_memory_mb': peak_memory_mb,
        'limit_mb': limit_mb,
        'within_limit': within_limit,
        'exceeded_by_mb': max(0, peak_memory_mb - limit_mb)
    }

def main():
    """Main entry point for memory monitoring."""
    monitor = MemoryMonitor(interval=0.5)
    monitor.start()
    
    # Simulate some work
    time.sleep(5)
    
    monitor.stop()
    
    peak = monitor.get_peak_memory_mb()
    result = verify_memory_limits(peak)
    
    print(f"Peak Memory: {peak:.2f} MB")
    print(f"Within 7GB limit: {result['within_limit']}")
    
    if not result['within_limit']:
        print(f"WARNING: Exceeded limit by {result['exceeded_by_mb']:.2f} MB")

if __name__ == "__main__":
    main()
