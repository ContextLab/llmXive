import time
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class TimeLimitExceededError(Exception):
    """Raised when execution time exceeds allowed limit."""
    pass

def start_timer() -> float:
    """
    Record the current time (in seconds since the epoch).
    
    Returns:
        float: The start time.
    """
    return time.time()

def check_time_limit(start_time: float, max_seconds: int = 6 * 60 * 60) -> None:
    """
    Check if the elapsed time since ``start_time`` exceeds ``max_seconds``.
    
    Args:
        start_time: The timestamp returned by ``start_timer``.
        max_seconds: Maximum allowed runtime in seconds (default 6 hours).
    
    Raises:
        TimeLimitExceededError: If the elapsed time exceeds the limit.
    """
    elapsed = time.time() - start_time
    if elapsed > max_seconds:
        raise TimeLimitExceededError(
            f"Time limit exceeded: {elapsed:.2f}s > {max_seconds}s"
        )
    logger.info(f"Time check passed: {elapsed:.2f}s elapsed, limit {max_seconds}s")

def main() -> None:
    """
    Simple CLI to demonstrate the time‑check utility.
    Use ``--sleep`` to simulate work and ``--max`` to set a custom limit.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Time limit checker")
    parser.add_argument(
        "--max",
        type=int,
        default=6 * 60 * 60,
        help="Maximum allowed seconds (default 6 hours)",
    )
    parser.add_argument(
        "--sleep",
        type=int,
        default=0,
        help="Number of seconds to sleep before checking (simulates work)",
    )
    args = parser.parse_args()

    start = start_timer()
    if args.sleep:
        time.sleep(args.sleep)

    try:
        check_time_limit(start, args.max)
        print("Time check passed.")
        sys.exit(0)
    except TimeLimitExceededError as e:
        print(f"Time check failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()