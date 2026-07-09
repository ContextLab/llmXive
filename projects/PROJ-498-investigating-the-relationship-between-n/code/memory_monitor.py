import os
import sys
import resource
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Constants
MEMORY_LIMIT_GB = 6.5
MEMORY_LIMIT_MB = MEMORY_LIMIT_GB * 1024
METRICS_DIR = Path("data/metrics")
LOG_FILE = Path("logs/processing.log")

def get_current_rss_mb() -> float:
    """
    Get the current Resident Set Size (RSS) of the process in megabytes.
    Uses resource module for Unix-like systems.
    """
    if sys.platform != "win32":
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in kilobytes on Linux/macOS
        return usage.ru_maxrss / 1024.0
    else:
        # Fallback for Windows (approximate)
        # Note: resource module is not available on Windows
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            # If psutil is not installed, return 0 or raise
            raise RuntimeError("Cannot get memory usage on Windows without psutil installed.")

def check_memory_limit(current_rss_mb: float, limit_mb: float = MEMORY_LIMIT_MB) -> bool:
    """
    Check if the current RSS is within the specified limit.
    Returns True if within limit, False otherwise.
    """
    return current_rss_mb <= limit_mb

def monitor_and_ensure_limit(subject_id: str, limit_mb: float = MEMORY_LIMIT_MB) -> bool:
    """
    Monitors memory usage for a specific subject processing step.
    If memory exceeds limit, logs a critical error and raises an exception.
    Returns True if within limits, False if exceeded (and exception raised).
    """
    current_rss = get_current_rss_mb()
    is_ok = check_memory_limit(current_rss, limit_mb)

    # Ensure logs directory exists
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] Memory Check - Subject: {subject_id}, RSS: {current_rss:.2f} MB, Limit: {limit_mb:.2f} MB, Status: {'OK' if is_ok else 'EXCEEDED'}"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

    if not is_ok:
        error_msg = f"CRITICAL: Memory limit exceeded for subject {subject_id}. RSS: {current_rss:.2f} MB > Limit: {limit_mb:.2f} MB. Halting pipeline."
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] ERROR: {error_msg}\n")
        print(error_msg, file=sys.stderr)
        raise MemoryError(error_msg)

    return True

class MemoryTracker:
    """
    A context manager and tracker for memory usage across a sequence of operations.
    Tracks peak memory usage and ensures it never exceeds the limit.
    """
    def __init__(self, limit_mb: float = MEMORY_LIMIT_MB):
        self.limit_mb = limit_mb
        self.peak_rss_mb = 0.0
        self.checkpoints: list = []

    def record(self, label: str = "") -> None:
        """Record current memory usage."""
        current = get_current_rss_mb()
        if current > self.peak_rss_mb:
            self.peak_rss_mb = current
        
        self.checkpoints.append({
            "label": label,
            "timestamp": datetime.now().isoformat(),
            "rss_mb": current
        })

        if current > self.limit_mb:
            raise MemoryError(f"Memory limit exceeded at checkpoint '{label}': {current:.2f} MB > {self.limit_mb:.2f} MB")

    def get_peak(self) -> float:
        return self.peak_rss_mb

    def is_within_limit(self) -> bool:
        return self.peak_rss_mb <= self.limit_mb

def save_memory_report(tracker: MemoryTracker, subject_id: str) -> None:
    """
    Saves the memory usage report for a subject to data/metrics/memory_report.json
    """
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = METRICS_DIR / f"memory_report_{subject_id}.json"

    report = {
        "subject_id": subject_id,
        "limit_mb": tracker.limit_mb,
        "peak_rss_mb": tracker.get_peak(),
        "status": "passed" if tracker.is_within_limit() else "failed",
        "checkpoints": tracker.checkpoints,
        "generated_at": datetime.now().isoformat()
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

def main():
    """
    Example usage for testing the memory monitor independently.
    Simulates processing a subject and checks memory limits.
    """
    print("Starting Memory Monitor Test...")
    tracker = MemoryTracker(limit_mb=MEMORY_LIMIT_MB)
    
    # Simulate some processing steps
    tracker.record("Initialization")
    time.sleep(0.1) # Simulate work
    tracker.record("Data Loading")
    
    # Simulate memory intensive operation (allocate large array)
    import numpy as np
    # Allocate 100MB to simulate memory usage increase
    dummy_data = np.zeros((25000000,), dtype=np.float64) 
    tracker.record("Simulated Heavy Processing")
    
    # Clean up
    del dummy_data
    tracker.record("Cleanup")

    # Save report
    save_memory_report(tracker, "TEST_SUBJECT")
    
    print(f"Peak Memory: {tracker.get_peak():.2f} MB")
    print(f"Limit: {tracker.limit_mb:.2f} MB")
    print(f"Status: {'PASS' if tracker.is_within_limit() else 'FAIL'}")
    print(f"Report saved to: {METRICS_DIR / 'memory_report_TEST_SUBJECT.json'}")

if __name__ == "__main__":
    main()