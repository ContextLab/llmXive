import os
import sys
import resource
import time
import json
from pathlib import Path
from typing import Optional

# Project root detection (assumes running from project root or code/ subdir)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
METRICS_DIR = DATA_DIR / "metrics"
LOGS_DIR = PROJECT_ROOT / "logs"

MEMORY_LIMIT_MB = 6500  # 6.5 GB

class MemoryTracker:
    """
    Tracks memory usage over time and ensures it does not exceed the limit.
    """
    def __init__(self):
        self.start_time = None
        self.max_rss_mb = 0.0
        self.history = [] # List of (timestamp, rss_mb)

    def start(self):
        """Start tracking."""
        self.start_time = time.time()
        self.max_rss_mb = 0.0
        self.history = []
        self._record()

    def _record(self):
        """Record current memory usage."""
        try:
            # resource.getrusage(resource.RUSAGE_SELF).ru_maxrss is in KB on Linux, MB on macOS
            # To be safe across platforms, we calculate KB and convert to MB
            usage = resource.getrusage(resource.RUSAGE_SELF)
            rss_kb = usage.ru_maxrss
            rss_mb = rss_kb / 1024.0
            
            if rss_mb > self.max_rss_mb:
                self.max_rss_mb = rss_mb
            
            self.history.append((time.time(), rss_mb))
        except Exception as e:
            # Fallback if resource module is unavailable (e.g., Windows)
            # Note: Windows resource.ru_maxrss is not standard, might need psutil
            # For this implementation, we assume Linux/macOS environment as per typical EEG pipelines
            pass

    def check_limit(self) -> bool:
        """
        Check if current memory usage exceeds the limit.
        Returns True if within limit, False if exceeded.
        """
        self._record()
        if self.max_rss_mb > MEMORY_LIMIT_MB:
            return False
        return True

    def get_max_rss_mb(self) -> float:
        """Return the peak RSS observed since start."""
        return self.max_rss_mb

    def save_report(self, filepath: Optional[Path] = None):
        """Save the memory report to a JSON file."""
        if filepath is None:
            METRICS_DIR.mkdir(parents=True, exist_ok=True)
            filepath = METRICS_DIR / "memory_report.json"
        
        report = {
            "start_time": self.start_time,
            "peak_rss_mb": self.max_rss_mb,
            "limit_mb": MEMORY_LIMIT_MB,
            "status": "ok" if self.max_rss_mb <= MEMORY_LIMIT_MB else "exceeded",
            "history": self.history
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)

def get_current_rss_mb() -> float:
    """Get current RSS in MB."""
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        rss_kb = usage.ru_maxrss
        return rss_kb / 1024.0
    except Exception:
        return 0.0

def check_memory_limit() -> bool:
    """
    Check if current memory usage is within the limit.
    Returns True if OK, False if exceeded.
    """
    current = get_current_rss_mb()
    return current <= MEMORY_LIMIT_MB

def monitor_and_ensure_limit(tracker: MemoryTracker) -> None:
    """
    Check memory limit and raise an error if exceeded.
    """
    if not tracker.check_limit():
        raise MemoryError(
            f"Memory limit exceeded: Peak RSS {tracker.get_max_rss_mb():.2f} MB > {MEMORY_LIMIT_MB} MB"
        )

def main():
    """
    Standalone test to demonstrate memory monitoring.
    Simulates processing and checks limits.
    """
    print("Starting Memory Monitor Test...")
    tracker = MemoryTracker()
    tracker.start()

    # Simulate some processing load
    import numpy as np
    print("Simulating data processing load...")
    for i in range(5):
        # Allocate some memory
        arr = np.random.rand(1000, 1000) # ~8MB per array
        del arr
        time.sleep(0.1)
        tracker._record()
        if not tracker.check_limit():
            print(f"Memory limit exceeded at step {i}")
            break
    
    print(f"Peak RSS: {tracker.get_max_rss_mb():.2f} MB")
    print(f"Limit: {MEMORY_LIMIT_MB} MB")
    
    # Save report
    report_path = METRICS_DIR / "memory_report.json"
    tracker.save_report(report_path)
    print(f"Memory report saved to {report_path}")

    if tracker.get_max_rss_mb() <= MEMORY_LIMIT_MB:
        print("SUCCESS: Memory usage within limits.")
        return 0
    else:
        print("FAILURE: Memory usage exceeded limits.")
        return 1

if __name__ == "__main__":
    sys.exit(main())