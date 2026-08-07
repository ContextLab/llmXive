"""
Verify that the pipeline runtime is within the allowed limit (7200 seconds).
This script reads output/pipeline_runtime.json and asserts status is 'pass'.
"""
import os
import sys
import json
from pathlib import Path

from utils.logging import get_logger

logger = get_logger(__name__)

def verify_runtime() -> bool:
    """
    Verify that output/pipeline_runtime.json exists, contains the required fields,
    and reports a status of 'pass' (total time <= 7200s).

    Returns:
        True if verification passes, False otherwise.
    """
    runtime_file = Path("output/pipeline_runtime.json")

    if not runtime_file.exists():
        logger.error(f"Runtime file not found: {runtime_file}")
        return False

    try:
        with open(runtime_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to read or parse {runtime_file}: {e}")
        return False

    required_fields = ["total_runtime_seconds", "limit_seconds", "status"]
    for field in required_fields:
        if field not in data:
            logger.error(f"Missing required field in runtime file: {field}")
            return False

    total_seconds = data["total_runtime_seconds"]
    limit_seconds = data["limit_seconds"]
    status = data["status"]

    logger.info(f"Total runtime: {total_seconds:.2f}s (limit: {limit_seconds}s)")
    logger.info(f"Status reported: {status}")

    if status != "pass":
        logger.error(f"Runtime verification FAILED: status is '{status}', expected 'pass'")
        return False

    if total_seconds > limit_seconds:
        logger.error(
            f"Runtime verification FAILED: {total_seconds}s exceeds limit of {limit_seconds}s"
        )
        return False

    logger.info("Runtime verification PASSED: total time <= limit and status is 'pass'")
    return True

def main() -> int:
    """Entry point for the script."""
    logger.info("Starting runtime verification (T120)...")
    success = verify_runtime()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
