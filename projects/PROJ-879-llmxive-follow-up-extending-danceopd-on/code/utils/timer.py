#!/usr/bin/env python
# Implementation
"""
Timer Utility.
Implements a configurable timeout using signal module.
"""
import signal
import time
import json
from pathlib import Path
from typing import Optional

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def setup_timeout(seconds: int):
    """Setup a timeout for the current process."""
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def cancel_timeout():
    """Cancel the active timeout."""
    signal.alarm(0)

def check_timeout(timeout_path: Path) -> bool:
    """Check if a timeout has occurred (for long running processes)."""
    if timeout_path.exists():
        with open(timeout_path, "r") as f:
            data = json.load(f)
            if data.get("timed_out"):
                return True
    return False

def save_timeout_status(timeout_path: Path, status: str = "partial"):
    """Save timeout status to a file."""
    timeout_path.parent.mkdir(parents=True, exist_ok=True)
    with open(timeout_path, "w") as f:
        json.dump({"timed_out": True, "status": status, "timestamp": time.time()}, f)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Timer utility")
    parser.add_argument("--seconds", type=int, default=60, help="Timeout duration")
    parser.add_argument("--output", type=str, default="data/results/timeout_status.json", help="Output path")
    args = parser.parse_args()
    
    timeout_path = Path(args.output)
    setup_timeout(args.seconds)
    
    try:
        time.sleep(args.seconds + 1) # Simulate work that times out
    except TimeoutError:
        print("Timeout occurred.")
        save_timeout_status(timeout_path)
        sys.exit(0)
    finally:
        cancel_timeout()

if __name__ == "__main__":
    import sys
    main()
