"""
Runtime monitoring and hard-stop enforcement for the analysis pipeline.

Implements FR-003 and SC-004:
- Hard stop at 6 hours runtime.
- "Time Limit Warning" at 5 hours.
- Integration with logging_config for warning emission.
"""
import os
import sys
import time
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

from config import get_runtime_limit_hours, get_warning_runtime_hours
from logging_config import log_memory_warning, get_logger

# Constants derived from config (defaults: 6h limit, 5h warning)
_START_TIME: Optional[float] = None
_LOGGER: Optional[logging.Logger] = None

def initialize_runtime_monitor() -> None:
    """
    Initialize the runtime monitor. Must be called at the start of the main pipeline.
    Sets the global start time and configures the logger.
    """
    global _START_TIME, _LOGGER
    _START_TIME = time.time()
    _LOGGER = get_logger("time_monitor")
    _LOGGER.info("Runtime monitoring initialized. Limit: %s hours, Warning: %s hours.",
                 get_runtime_limit_hours(), get_warning_runtime_hours())

def check_runtime_status() -> bool:
    """
    Checks the current runtime against limits.
    
    Returns:
        bool: True if the process should continue, False if hard stop limit reached.
    
    Side effects:
        - Logs a "Time Limit Warning" if warning threshold is crossed but not exceeded.
        - Logs a fatal error and raises SystemExit if hard stop threshold is reached.
    """
    if _START_TIME is None:
        # Monitor not initialized, allow execution
        return True

    if _LOGGER is None:
        _LOGGER = get_logger("time_monitor")

    current_time = time.time()
    elapsed_seconds = current_time - _START_TIME
    elapsed_hours = elapsed_seconds / 3600.0

    limit_hours = get_runtime_limit_hours()
    warning_hours = get_warning_runtime_hours()

    # Check Hard Stop first
    if elapsed_hours >= limit_hours:
        _LOGGER.critical(
            "TIME LIMIT EXCEEDED: Runtime %.2f hours exceeds hard limit of %.2f hours. "
            "Initiating hard stop to prevent resource overuse (SC-004).",
            elapsed_hours, limit_hours
        )
        raise SystemExit(f"Hard stop: Runtime limit ({limit_hours}h) exceeded. Elapsed: {elapsed_hours:.2f}h")

    # Check Warning Threshold
    if elapsed_hours >= warning_hours:
        # Log a warning specifically formatted as requested
        warning_msg = (
            f"Time Limit Warning: Runtime {elapsed_hours:.2f} hours has exceeded "
            f"warning threshold of {warning_hours} hours. Approaching hard stop at {limit_hours}h."
        )
        # Use the specific logging hook mechanism if available, otherwise standard critical/warning
        log_memory_warning(warning_msg) # Reusing the hook mechanism for consistency
        _LOGGER.warning(warning_msg)
        
        # Log a specific marker for easy parsing by the final report generator
        _LOGGER.warning("MARKER: TIME_LIMIT_WARNING_TRIGGERED")

    return True

def get_elapsed_time_hours() -> float:
    """Returns the elapsed time in hours since initialization."""
    if _START_TIME is None:
        return 0.0
    return (time.time() - _START_TIME) / 3600.0

def ensure_runtime_limit() -> None:
    """
    Convenience wrapper to check status and exit if necessary.
    To be called periodically in long-running loops.
    """
    if not check_runtime_status():
        # Should not be reachable as check_runtime_status raises SystemExit
        sys.exit(1)

def main():
    """
    CLI entry point for testing the time monitor independently.
    Usage: python code/time_monitor.py [--duration <hours>]
    """
    import argparse
    parser = argparse.ArgumentParser(description="Test runtime monitor hard stop and warnings.")
    parser.add_argument("--duration", type=float, default=6.5, help="Duration to run in hours.")
    parser.add_argument("--warning", type=float, default=5.0, help="Warning threshold in hours.")
    args = parser.parse_args()

    # Temporarily override config for testing if needed, or just use defaults
    # For this test, we simulate the passage of time or just check logic
    # Since we can't wait 6 hours in a test, we simulate the check logic
    
    initialize_runtime_monitor()
    
    # Simulate a check at various points
    test_points = [4.0, 4.9, 5.0, 5.1, 5.9, 6.1]
    
    print(f"Testing runtime monitor with limit={args.duration}h, warning={args.warning}h")
    
    # We will mock the start time to simulate elapsed time
    # Reset start time to simulate 'now' being 0, then we manually adjust _START_TIME
    global _START_TIME
    base_time = time.time()
    
    for test_elapsed in test_points:
        _START_TIME = base_time - (test_elapsed * 3600)
        try:
            result = check_runtime_status()
            print(f"Elapsed: {test_elapsed}h -> Status: Continue ({result})")
        except SystemExit as e:
            print(f"Elapsed: {test_elapsed}h -> HARD STOP: {e}")
            break

    print("Time monitor test completed.")

if __name__ == "__main__":
    main()
