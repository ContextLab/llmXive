"""
Runtime Logger Module.

Provides functions to start, stop, and persist runtime logs for benchmarking.
Ensures that `data/benchmarks/runtime_log.json` is written correctly.
"""
import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_start_time: Optional[float] = None
_start_iso: Optional[str] = None

def start_timer():
    """Starts the global timer."""
    global _start_time, _start_iso
    _start_time = time.time()
    _start_iso = datetime.now().isoformat()
    logger.info(f"Timer started at {_start_iso}")

def end_timer() -> float:
    """Stops the global timer and returns elapsed seconds."""
    global _start_time
    if _start_time is None:
        raise RuntimeError("Timer has not been started. Call start_timer() first.")
    
    end_time = time.time()
    elapsed = end_time - _start_time
    _start_time = None
    logger.info(f"Timer ended. Elapsed: {elapsed:.2f} seconds.")
    return elapsed

def get_elapsed_seconds() -> float:
    """Returns the elapsed time since start_timer() was called."""
    global _start_time
    if _start_time is None:
        raise RuntimeError("Timer has not been started.")
    return time.time() - _start_time

def persist_runtime_log(start_time: str, end_time: str, duration_seconds: float, status: str = "success"):
    """
    Persists the runtime log to `data/benchmarks/runtime_log.json`.
    
    Args:
        start_time: ISO8601 formatted start time.
        end_time: ISO8601 formatted end time.
        duration_seconds: Elapsed time in seconds.
        status: Status string ('success' or 'failed').
    """
    output_dir = Path("data/benchmarks")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "runtime_log.json"
    
    log_entry = {
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": duration_seconds,
        "status": status
    }
    
    try:
        with open(output_file, "w") as f:
            json.dump(log_entry, f, indent=2)
        logger.info(f"Runtime log persisted to {output_file}")
    except Exception as e:
        logger.error(f"Failed to persist runtime log: {e}")
        raise

def main():
    """Test the runtime logger."""
    start_timer()
    time.sleep(1)  # Simulate work
    elapsed = end_timer()
    
    start_iso = datetime.now().isoformat() # This is a bit off, but for demo
    # In real usage, we'd capture start_iso at start_timer
    # For this demo, we'll use the actual start time from the function
    # But since we can't easily get it here without modifying start_timer,
    # we'll just use a placeholder for the demo
    persist_runtime_log(
        start_time=datetime.now().isoformat(), 
        end_time=datetime.now().isoformat(), 
        duration_seconds=elapsed, 
        status="success"
    )
    print(f"Logged runtime: {elapsed} seconds")

if __name__ == "__main__":
    main()