import json
import time
import threading
from functools import wraps
from pathlib import Path
from typing import Callable, Optional

# Ensure the results directory exists at module load time or on first use
RESULTS_DIR = Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
VIOLATIONS_FILE = RESULTS_DIR / "latency_violations.json"

# Thread-local storage for violation accumulation to ensure thread safety
_local = threading.local()

def _get_violations():
    if not hasattr(_local, 'violations'):
        _local.violations = []
    return _local.violations

def _save_violations():
    """Persist accumulated violations to disk."""
    violations = _get_violations()
    if violations:
        # Load existing to append if file exists, otherwise start fresh
        existing = []
        if VIOLATIONS_FILE.exists():
            try:
                with open(VIOLATIONS_FILE, 'r') as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, IOError):
                existing = []
        
        # Append new violations
        existing.extend(violations)
        
        # Write back atomically
        with open(VIOLATIONS_FILE, 'w') as f:
            json.dump(existing, f, indent=2)
        
        # Clear thread-local storage after saving
        _local.violations = []

def latency_guard(limit_ms: int):
    """
    Decorator to measure function execution latency.
    
    If the function execution time exceeds `limit_ms`, the violation is logged
    to `data/results/latency_violations.json` and the function continues normally
    (does not raise an exception).
    
    Args:
        limit_ms: Maximum allowed execution time in milliseconds.
    
    Returns:
        Decorated function that measures and logs latency violations.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                
                if duration_ms > limit_ms:
                    violation_entry = {
                        "function_name": func.__name__,
                        "limit_ms": limit_ms,
                        "actual_duration_ms": round(duration_ms, 3),
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    }
                    
                    # Accumulate in thread-local storage
                    current_violations = _get_violations()
                    current_violations.append(violation_entry)
                    
                    # Save to disk periodically or immediately
                    # For robustness, save immediately to avoid data loss on crash
                    _save_violations()
                    
        return wrapper
    return decorator

def flush_violations():
    """
    Explicitly flush any accumulated violations to disk.
    Useful for testing or ensuring data is written before exit.
    """
    _save_violations()