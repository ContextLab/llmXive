import os
import sys
import resource
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Constants
MEMORY_LIMIT_GB = 6.5
MEMORY_LIMIT_MB = MEMORY_LIMIT_GB * 1024
METRICS_DIR = Path("data/metrics")
LOG_FILE = Path("logs/processing.log")

def get_current_rss_mb() -> float:
    """
    Get the current Resident Set Size (RSS) of the process in Megabytes.
    Uses resource module (Unix) or falls back to psutil if available (cross-platform).
    """
    try:
        # Unix/Linux/macOS
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in kilobytes on Linux/macOS, but bytes on some systems.
        # On Linux, it is KB. On macOS, it is bytes (usually).
        # Standard convention for resource.getrusage on Linux: KB.
        maxrss_kb = usage.ru_maxrss
        return maxrss_kb / 1024.0
    except Exception:
        # Fallback for Windows or if resource fails
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            raise RuntimeError(
                "Could not determine memory usage. Install 'psutil' or run on a Unix-like system."
            )

def check_memory_limit(current_rss_mb: float, limit_mb: float = MEMORY_LIMIT_MB) -> bool:
    """
    Check if current RSS exceeds the limit.
    Returns True if within limit, False if exceeded.
    """
    return current_rss_mb <= limit_mb

def monitor_and_ensure_limit(limit_mb: float = MEMORY_LIMIT_MB) -> None:
    """
    Checks the current memory usage. If it exceeds the limit, raises a RuntimeError.
    This is intended to be called after processing a subject or a batch.
    """
    current = get_current_rss_mb()
    if not check_memory_limit(current, limit_mb):
        raise RuntimeError(
            f"Memory limit exceeded: Current RSS {current:.2f} MB > Limit {limit_mb:.2f} MB. "
            "Processing halted to prevent OOM."
        )

class MemoryTracker:
    """
    Tracks memory usage over time during processing.
    Records peak RSS and timestamps.
    """
    def __init__(self, limit_mb: float = MEMORY_LIMIT_MB):
        self.limit_mb = limit_mb
        self.peak_rss_mb = 0.0
        self.samples: list[Dict[str, Any]] = []
        self.start_time: Optional[float] = None

    def start(self):
        self.start_time = time.time()
        self.peak_rss_mb = 0.0
        self.samples = []

    def record(self, step_name: str = ""):
        current = get_current_rss_mb()
        if current > self.peak_rss_mb:
            self.peak_rss_mb = current

        self.samples.append({
            "step": step_name,
            "timestamp": time.time() - (self.start_time or time.time()),
            "rss_mb": current
        })

        # Check limit immediately
        if not check_memory_limit(current, self.limit_mb):
            raise RuntimeError(
                f"Memory limit exceeded at step '{step_name}': "
                f"RSS {current:.2f} MB > Limit {self.limit_mb:.2f} MB."
            )

    def get_peak(self) -> float:
        return self.peak_rss_mb

    def save_report(self, output_path: Optional[Path] = None) -> Path:
        """
        Saves the memory tracking report to a JSON file.
        """
        if output_path is None:
            METRICS_DIR.mkdir(parents=True, exist_ok=True)
            output_path = METRICS_DIR / "memory_report.json"
        
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "peak_rss_mb": self.peak_rss_mb,
            "limit_mb": self.limit_mb,
            "status": "passed" if self.peak_rss_mb <= self.limit_mb else "failed",
            "samples": self.samples
        }

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return output_path

def save_memory_report(tracker: MemoryTracker, output_path: Optional[Path] = None) -> Path:
    """
    Wrapper to save the tracker's report.
    """
    return tracker.save_report(output_path)

def main():
    """
    Standalone test for memory monitoring.
    Simulates processing and checks limits.
    """
    print("Starting Memory Monitor Test...")
    tracker = MemoryTracker(limit_mb=MEMORY_LIMIT_MB)
    tracker.start()

    try:
        # Simulate some work
        import numpy as np
        for i in range(5):
            # Allocate some memory to simulate subject processing
            data = np.random.rand(10000000) # ~80MB per iteration
            tracker.record(f"simulated_step_{i}")
            # Release memory
            del data
            time.sleep(0.1)
        
        peak = tracker.get_peak()
        print(f"Peak RSS: {peak:.2f} MB (Limit: {MEMORY_LIMIT_MB} MB)")
        
        if peak <= MEMORY_LIMIT_MB:
            print("Memory check PASSED.")
        else:
            print("Memory check FAILED.")
        
        report_path = tracker.save_report()
        print(f"Report saved to: {report_path}")

    except RuntimeError as e:
        print(f"CRITICAL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()