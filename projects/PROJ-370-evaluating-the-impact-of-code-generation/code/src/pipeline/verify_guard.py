import time
import sys
from pathlib import Path
from src.pipeline.runtime_guard import RuntimeGuard
from llmxive_toolkit import paths

def main():
    """
    Verification script to demonstrate that RuntimeGuard:
    1. Exits with code 143 when the deadline has passed.
    2. Writes a timeout event to logs/timeout.log.
    """
    # 1. Set a deadline 10 seconds in the past.
    deadline = time.time() - 10
    guard = RuntimeGuard(deadline_ts=deadline)

    print(f"Triggering RuntimeGuard with past deadline: {deadline}")
    
    # We catch the SystemExit to verify the code and the file, 
    # then exit 0 so the pipeline runner knows the verification succeeded.
    try:
        guard.check()
        print("FAIL: Guard did not trigger SystemExit")
        sys.exit(1)
    except SystemExit as e:
        if e.code != 143:
            print(f"FAIL: Guard exited with {e.code}, expected 143")
            sys.exit(1)
        print("SUCCESS: Guard exited with code 143")

    # 2. Verify the log file exists and contains the timeout event.
    log_path = paths.logs("timeout.log")
    if log_path.exists() and log_path.stat().st_size > 0:
        print(f"SUCCESS: {log_path} created and is non-empty")
    else:
        print(f"FAIL: {log_path} missing or empty")
        sys.exit(1)

if __name__ == "__main__":
    main()