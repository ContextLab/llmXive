import os
import sys
import resource
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from functools import wraps

from config import ensure_directories

# Constants
MEMORY_LIMIT_GB = 6.5
MEMORY_LIMIT_MB = MEMORY_LIMIT_GB * 1024
METRICS_PATH = Path("data/metrics/memory_profile.json")

def ensure_metrics_directory():
    """Ensure the metrics directory exists."""
    ensure_directories()
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_current_rss_mb() -> float:
    """
    Get the current Resident Set Size (RSS) of the process in MB.
    Uses resource.getrusage for Unix-like systems.
    """
    try:
        # ru_maxrss is in KB on Linux, but in bytes on macOS (sometimes).
        # Standard Linux returns KB. We convert to MB.
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, MB on some BSDs/macOS depending on version.
        # We assume Linux standard (KB) first, then check if it's suspiciously large.
        maxrss_kb = usage.ru_maxrss
        
        # Heuristic: If value is > 100,000, it might be in bytes (100GB+), 
        # or if < 1000 it might be MB (unlikely for RSS). 
        # On standard Linux, RSS is in KB.
        # Let's normalize: Assume KB.
        return maxrss_kb / 1024.0
    except AttributeError:
        # Fallback for non-Unix systems (e.g., Windows) if necessary, 
        # though resource module is Unix-specific.
        # For Windows, one might use psutil, but we stick to stdlib for now.
        logging.warning("resource.getrusage not available; cannot measure RSS.")
        return 0.0

def check_memory_limit(current_mb: float) -> bool:
    """
    Check if current memory usage exceeds the limit.
    Returns True if OK, False if limit exceeded.
    """
    return current_mb <= MEMORY_LIMIT_MB

def log_memory_usage(subject_id: str, current_mb: float, peak_mb: float):
    """Log current memory usage to the processing log."""
    logger = logging.getLogger(__name__)
    logger.info(f"Subject {subject_id}: Current RSS = {current_mb:.2f} MB, Peak RSS = {peak_mb:.2f} MB")

def save_memory_profile(profile_data: Dict[str, Any]):
    """Save the memory profile to the JSON file."""
    ensure_metrics_directory()
    with open(METRICS_PATH, 'w') as f:
        json.dump(profile_data, f, indent=2)

class MemoryTracker:
    """
    Context manager and utility class to track memory usage per subject.
    Ensures peak RSS <= 6.5 GB and records metrics.
    """
    def __init__(self, profile_path: Optional[Path] = None):
        self.profile_path = profile_path or METRICS_PATH
        self.profile_data: Dict[str, Any] = {
            "limit_gb": MEMORY_LIMIT_GB,
            "subjects": {}
        }
        self._start_rss: float = 0.0
        self._peak_rss: float = 0.0
        self._current_subject: Optional[str] = None

    def load_existing_profile(self):
        """Load existing profile if it exists to append new data."""
        if self.profile_path.exists():
            try:
                with open(self.profile_path, 'r') as f:
                    self.profile_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.profile_data = {
                    "limit_gb": MEMORY_LIMIT_GB,
                    "subjects": {}
                }

    def start_subject(self, subject_id: str):
        """Record start memory for a subject."""
        self._current_subject = subject_id
        self._start_rss = get_current_rss_mb()
        # Initialize subject entry if new
        if subject_id not in self.profile_data["subjects"]:
            self.profile_data["subjects"][subject_id] = {
                "start_mb": self._start_rss,
                "peak_mb": 0.0,
                "status": "processing"
            }
        # Update peak if current is higher
        if self._start_rss > self._peak_rss:
            self._peak_rss = self._start_rss

    def update_peak(self):
        """Update the running peak memory for the current subject."""
        current = get_current_rss_mb()
        if current > self._peak_rss:
            self._peak_rss = current
        
        # Check limit immediately
        if not check_memory_limit(current):
            raise MemoryError(
                f"Memory limit exceeded! "
                f"Subject: {self._current_subject}, "
                f"Current RSS: {current:.2f} MB, "
                f"Limit: {MEMORY_LIMIT_MB:.2f} MB ({MEMORY_LIMIT_GB} GB). "
                f"HALTING execution as per SC-001."
            )

    def finish_subject(self):
        """Finalize memory tracking for the current subject."""
        if not self._current_subject:
            return

        # Final update
        self.update_peak()
        
        # Record in profile
        self.profile_data["subjects"][self._current_subject].update({
            "peak_mb": self._peak_rss,
            "status": "completed"
        })
        
        log_memory_usage(self._current_subject, get_current_rss_mb(), self._peak_rss)
        
        # Save incrementally to ensure data is not lost if crash occurs later
        self.save_profile()

    def save_profile(self):
        """Save the current state of the profile to disk."""
        save_memory_profile(self.profile_data)

    def __enter__(self):
        self.load_existing_profile()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.save_profile()
        return False

def monitor_and_ensure_limit(func: Callable) -> Callable:
    """
    Decorator to monitor memory usage during a function execution.
    Raises MemoryError if limit is exceeded.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract subject_id from args or kwargs if available, else use 'unknown'
        subject_id = "unknown"
        if args and isinstance(args[0], str):
            subject_id = args[0]
        elif 'subject_id' in kwargs:
            subject_id = kwargs['subject_id']

        tracker = MemoryTracker()
        tracker.load_existing_profile()
        tracker.start_subject(subject_id)
        
        try:
            result = func(*args, **kwargs)
            tracker.finish_subject()
            return result
        except MemoryError:
            # Re-raise to halt execution
            raise
        except Exception as e:
            # Ensure we save partial data even on other errors
            tracker.profile_data["subjects"][subject_id]["status"] = "failed"
            tracker.save_profile()
            raise
    return wrapper

def main():
    """
    Main entry point for standalone memory monitoring test.
    """
    print("Memory Monitor Utility")
    print(f"Limit: {MEMORY_LIMIT_GB} GB ({MEMORY_LIMIT_MB} MB)")
    
    # Test current RSS
    rss = get_current_rss_mb()
    print(f"Current RSS: {rss:.2f} MB")
    print(f"Limit check: {'PASS' if check_memory_limit(rss) else 'FAIL'}")
    
    # Test profile saving
    with MemoryTracker() as tracker:
        tracker.start_subject("test-subject")
        time.sleep(0.1) # Simulate work
        tracker.update_peak()
        tracker.finish_subject()
    
    print(f"Profile saved to: {METRICS_PATH}")
    if METRICS_PATH.exists():
        with open(METRICS_PATH, 'r') as f:
            print(f.read())

if __name__ == "__main__":
    main()