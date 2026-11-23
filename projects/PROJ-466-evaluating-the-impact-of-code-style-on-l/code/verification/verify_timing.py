"""
Verification module for T044a and T044b.
Verifies that data/logs/timing.log exists and contains a duration < 6 hours.
"""
import os
import sys
import re
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_timing_log(project_root: Path = None) -> bool:
    """
    Verify that data/logs/timing.log exists and contains a valid duration < 6 hours.

    Args:
        project_root: The root directory of the project. Defaults to current working directory.

    Returns:
        True if verification passes, False otherwise.

    Raises:
        FileNotFoundError: If the timing.log file does not exist.
        ValueError: If the duration cannot be parsed or exceeds 6 hours.
    """
    if project_root is None:
        project_root = Path.cwd()

    log_path = project_root / "data" / "logs" / "timing.log"

    # Check if file exists
    if not log_path.exists():
        logger.error(f"Timing log not found at: {log_path}")
        raise FileNotFoundError(f"Required artifact missing: {log_path}")

    logger.info(f"Found timing log at: {log_path}")

    # Read the file content
    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()

    logger.info(f"Content of timing.log:\n{content}")

    # Pattern to match duration (e.g., "Duration: 3.5 hours" or "Duration: 120 minutes")
    # We look for a number associated with hours, minutes, or seconds
    duration_hours = None

    # Try to find "Duration: X hours"
    hours_match = re.search(r'Duration:\s*([\d.]+)\s*hours?', content, re.IGNORECASE)
    if hours_match:
        duration_hours = float(hours_match.group(1))
    else:
        # Try minutes
        minutes_match = re.search(r'Duration:\s*([\d.]+)\s*minutes?', content, re.IGNORECASE)
        if minutes_match:
            duration_hours = float(minutes_match.group(1)) / 60.0
        else:
            # Try seconds
            seconds_match = re.search(r'Duration:\s*([\d.]+)\s*seconds?', content, re.IGNORECASE)
            if seconds_match:
                duration_hours = float(seconds_match.group(1)) / 3600.0

    if duration_hours is None:
        # Fallback: look for any number followed by time unit if specific pattern fails
        # Or raise error if we can't parse
        logger.error("Could not parse duration from timing log.")
        raise ValueError("Could not parse duration from timing log.")

    threshold_hours = 6.0

    logger.info(f"Parsed duration: {duration_hours:.2f} hours")
    logger.info(f"Threshold: {threshold_hours} hours")

    if duration_hours >= threshold_hours:
        logger.error(f"Duration {duration_hours:.2f} hours exceeds threshold of {threshold_hours} hours.")
        raise ValueError(f"Pipeline execution took {duration_hours:.2f} hours, exceeding the 6-hour limit.")

    logger.info(f"Verification PASSED: Duration {duration_hours:.2f} hours is within the 6-hour limit.")
    return True

def main():
    """Main entry point for verification script."""
    try:
        project_root = Path.cwd()
        success = verify_timing_log(project_root)
        if success:
            print("SUCCESS: T044b verification passed.")
            sys.exit(0)
        else:
            print("FAILURE: T044b verification failed.")
            sys.exit(1)
    except FileNotFoundError as e:
        print(f"FAILURE: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"FAILURE: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"FAILURE: Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()