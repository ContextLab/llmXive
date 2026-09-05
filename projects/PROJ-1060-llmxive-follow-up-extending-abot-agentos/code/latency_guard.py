import json
import time
import threading
from functools import wraps
from pathlib import Path
from typing import Callable, Optional, List, Dict, Any

VIOLATIONS_FILE = Path("data/results/latency_violations.json")
_violations: List[Dict[str, Any]] = []
_lock = threading.Lock()

def _ensure_dir():
    VIOLATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)

def _persist_violations():
    _ensure_dir()
    with open(VIOLATIONS_FILE, 'w') as f:
        json.dump(_violations, f, indent=2)

def latency_guard(threshold_ms: float = 100.0):
    """
    Decorator to measure query latency.
    If limit exceeded, log violation to data/results/latency_violations.json
    and continue (do NOT fail the run).
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = (time.perf_counter() - start) * 1000
                if elapsed > threshold_ms:
                    with _lock:
                        _violations.append({
                            "query_id": getattr(func, '__name__', 'unknown'),
                            "latency_ms": round(elapsed, 3),
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        })
                        _persist_violations()
        return wrapper
    return decorator

def flush_violations():
    global _violations
    with _lock:
        _violations = []
    if VIOLATIONS_FILE.exists():
        VIOLATIONS_FILE.unlink()

def main():
    """
    Demo entry point to verify the decorator writes to disk.
    Simulates a query that exceeds the threshold to prove functionality.
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    # Ensure output directory exists
    _ensure_dir()

    @latency_guard(threshold_ms=10.0)
    def slow_query():
        time.sleep(0.05)  # Sleep for 50ms, exceeding 10ms threshold
        return "result"

    @latency_guard(threshold_ms=1000.0)
    def fast_query():
        time.sleep(0.001)  # Sleep for 1ms, well under 1000ms threshold
        return "result"

    # Run queries
    print("Running slow_query (expected violation)...")
    slow_query()

    print("Running fast_query (expected no violation)...")
    fast_query()

    # Verify file creation
    if VIOLATIONS_FILE.exists():
        with open(VIOLATIONS_FILE, 'r') as f:
            data = json.load(f)
        print(f"Violations logged: {len(data)}")
        print(f"Content: {json.dumps(data, indent=2)}")
    else:
        print("ERROR: Violations file not created.")

if __name__ == "__main__":
    main()