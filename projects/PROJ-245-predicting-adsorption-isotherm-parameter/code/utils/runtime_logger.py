import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

_start_time: Optional[float] = None
_start_iso: Optional[str] = None

def start_timer() -> None:
    """Start the runtime timer and record the ISO8601 start time."""
    global _start_time, _start_iso
    _start_time = time.time()
    _start_iso = datetime.utcnow().isoformat() + 'Z'
    logger.info("Runtime timer started.")

def end_timer() -> Optional[float]:
    """Stop the timer and return the elapsed seconds. Returns None if timer wasn't started."""
    global _start_time
    if _start_time is None:
        logger.warning("Timer end called but timer was not started.")
        return None
    elapsed = time.time() - _start_time
    _start_time = None  # Reset
    logger.info(f"Runtime timer ended. Elapsed: {elapsed:.2f}s")
    return elapsed

def get_elapsed_seconds() -> Optional[float]:
    """Get the elapsed seconds since start. Returns None if timer not started."""
    global _start_time
    if _start_time is None:
        return None
    return time.time() - _start_time

def persist_runtime_log(
    output_path: str,
    status: str = "success",
    extra_metrics: Optional[Dict[str, Any]] = None
) -> None:
    """
    Persist the runtime log to a JSON file.
    
    Args:
        output_path: Path to the output JSON file (e.g., data/benchmarks/runtime_log.json).
        status: Status string ('success', 'failed', 'partial').
        extra_metrics: Optional dictionary of additional metrics to include.
    """
    global _start_iso
    
    elapsed = get_elapsed_seconds() if _start_time is not None else None
    if elapsed is None and _start_iso:
        # Timer was stopped, calculate elapsed via end_timer logic if needed, 
        # but usually end_timer is called before persist.
        # If we are here and _start_time is None, we rely on the fact that 
        # end_timer was called and we need to retrieve the value.
        # However, end_timer returns the value. 
        # To support calling persist after end_timer without capturing the return,
        # we assume the caller passed the elapsed time or we need to store it globally.
        # Let's store the last elapsed time globally.
        pass

    # We need to store the last elapsed time to persist it if end_timer was called.
    # Let's add a global for the last elapsed duration.
    pass

# Refactoring to support state persistence correctly
_last_elapsed: Optional[float] = None
_last_status: str = "unknown"
_last_iso_end: Optional[str] = None

def start_timer() -> None:
    """Start the runtime timer and record the ISO8601 start time."""
    global _start_time, _start_iso, _last_elapsed
    _start_time = time.time()
    _start_iso = datetime.utcnow().isoformat() + 'Z'
    _last_elapsed = None
    logger.info("Runtime timer started.")

def end_timer() -> Optional[float]:
    """Stop the timer, store the elapsed time, and return it."""
    global _start_time, _last_elapsed, _last_iso_end
    if _start_time is None:
        logger.warning("Timer end called but timer was not started.")
        return None
    
    elapsed = time.time() - _start_time
    _last_elapsed = elapsed
    _last_iso_end = datetime.utcnow().isoformat() + 'Z'
    _start_time = None
    logger.info(f"Runtime timer ended. Elapsed: {elapsed:.2f}s")
    return elapsed

def get_elapsed_seconds() -> Optional[float]:
    """Get the elapsed seconds since start. Returns None if timer not started."""
    global _start_time
    if _start_time is None:
        return _last_elapsed
    return time.time() - _start_time

def persist_runtime_log(
    output_path: str,
    status: str = "success",
    extra_metrics: Optional[Dict[str, Any]] = None
) -> None:
    """
    Persist the runtime log to a JSON file.
    
    Args:
        output_path: Path to the output JSON file (e.g., data/benchmarks/runtime_log.json).
        status: Status string ('success', 'failed', 'partial').
        extra_metrics: Optional dictionary of additional metrics to include.
    """
    global _start_iso, _last_iso_end, _last_elapsed, _last_status
    
    elapsed = get_elapsed_seconds()
    if elapsed is None:
        elapsed = 0.0
        
    log_entry = {
        "start_time": _start_iso or datetime.utcnow().isoformat() + 'Z',
        "end_time": _last_iso_end or datetime.utcnow().isoformat() + 'Z',
        "duration_seconds": elapsed,
        "status": status
    }
    
    if extra_metrics:
        log_entry.update(extra_metrics)
    
    # Ensure directory exists
    path_obj = Path(output_path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path_obj, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    logger.info(f"Runtime log persisted to {output_path}")

def main():
    """Example usage for standalone testing."""
    start_timer()
    time.sleep(1)  # Simulate work
    end_timer()
    persist_runtime_log("data/benchmarks/runtime_log.json", status="success")
    print("Runtime log generated.")

if __name__ == "__main__":
    main()
