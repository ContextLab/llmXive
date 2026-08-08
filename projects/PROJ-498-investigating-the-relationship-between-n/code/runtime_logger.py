import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Import from existing project modules if needed, though this module is self-contained
# Ensure it can be imported without errors even if other modules fail
try:
    from config import ensure_directories
except ImportError:
    ensure_directories = None

METRICS_DIR = Path("data/metrics")
LOG_FILE = METRICS_DIR / "runtime_log.json"
PROCESSING_LOG = Path("logs/processing.log")

_start_time: float | None = None
_start_datetime: datetime | None = None

def ensure_metrics_directory():
    """Ensure the metrics directory exists."""
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    # Also ensure logs directory exists if we need to write there
    Path("logs").mkdir(parents=True, exist_ok=True)

def start_timer():
    """Start the runtime timer."""
    global _start_time, _start_datetime
    _start_time = time.time()
    _start_datetime = datetime.now()
    return _start_time

def get_elapsed_minutes():
    """Get the elapsed time in minutes since start_timer was called."""
    if _start_time is None:
        return 0.0
    elapsed_seconds = time.time() - _start_time
    return elapsed_seconds / 60.0

def save_runtime_log(status: str = "success"):
    """
    Save the runtime log to data/metrics/runtime_log.json.
    
    Args:
        status: Either 'success' or 'timeout'
    """
    ensure_metrics_directory()
    
    if _start_datetime is None:
        # If timer was never started, use current time for both
        now = datetime.now()
        start_dt = now
        duration = 0.0
    else:
        start_dt = _start_datetime
        duration = get_elapsed_minutes()
    
    end_dt = datetime.now()
    
    log_entry = {
        "start_time": start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "end_time": end_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_duration_minutes": round(duration, 2),
        "status": status
    }
    
    # Write to JSON file
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_entry, f, indent=2)
    
    # Also log to processing.log if it exists or can be created
    try:
        with open(PROCESSING_LOG, 'a', encoding='utf-8') as log_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"[{timestamp}] Runtime log saved: status={status}, duration={duration:.2f} minutes\n")
    except Exception:
        # If logging fails, we still saved the JSON, which is the primary requirement
        pass
    
    return log_entry

def main():
    """
    Main function to demonstrate runtime logging.
    Can be used to test the logger independently.
    """
    print("Starting runtime logger test...")
    start_timer()
    
    # Simulate some work
    time.sleep(1)
    
    # Save as success
    result = save_runtime_log("success")
    print(f"Runtime log saved: {result}")
    
    # Verify file exists
    if LOG_FILE.exists():
        print(f"Verified: {LOG_FILE} exists")
        with open(LOG_FILE, 'r') as f:
            print(f"Contents: {f.read()}")
    else:
        print(f"ERROR: {LOG_FILE} was not created")
        sys.exit(1)

if __name__ == "__main__":
    main()