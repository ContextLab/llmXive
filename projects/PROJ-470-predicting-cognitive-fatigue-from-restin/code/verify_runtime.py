"""Runtime verification script for T028.

Verifies that the total pipeline runtime is <= 6 hours (SC-002).
Reads resource usage from data/analysis/resource_usage.json.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Import the logger from the shared utility
# Note: The project uses code/utils/logging.py for the shared logger
try:
    from utils.logging import get_logger
except ImportError:
    # Fallback if utils.logging is not available (should not happen in correct setup)
    import logging as stdlib_logging
    _logger = stdlib_logging.getLogger("verify_runtime")
    def get_logger(*args, **kwargs):
        return _logger

MAX_RUNTIME_HOURS = 6.0
RESOURCE_USAGE_FILE = "data/analysis/resource_usage.json"


def load_resource_usage(filepath: str) -> dict:
    """Load the resource usage JSON file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Resource usage file not found: {filepath}")
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_runtime(resource_data: dict, max_hours: float = MAX_RUNTIME_HOURS) -> bool:
    """Verify that total_runtime_hours is within the limit.
    
    Args:
        resource_data: Dictionary containing 'total_runtime_hours'.
        max_hours: Maximum allowed runtime in hours.
        
    Returns:
        True if runtime is within limit, False otherwise.
    """
    runtime = resource_data.get("total_runtime_hours")
    if runtime is None:
        raise ValueError("Resource usage data missing 'total_runtime_hours' key")
    
    logger = get_logger("verify_runtime")
    logger.info(f"Total runtime: {runtime:.2f} hours")
    logger.info(f"Maximum allowed runtime: {max_hours:.2f} hours")
    
    if runtime <= max_hours:
        logger.info("Runtime verification PASSED")
        return True
    else:
        logger.error("Runtime verification FAILED: Exceeded maximum allowed runtime")
        return False


def main():
    """Main entry point for runtime verification."""
    parser = argparse.ArgumentParser(description="Verify pipeline runtime limits")
    parser.add_argument(
        "--resource-file",
        type=str,
        default=RESOURCE_USAGE_FILE,
        help=f"Path to resource usage JSON file (default: {RESOURCE_USAGE_FILE})"
    )
    parser.add_argument(
        "--max-hours",
        type=float,
        default=MAX_RUNTIME_HOURS,
        help=f"Maximum allowed runtime in hours (default: {MAX_RUNTIME_HOURS})"
    )
    args = parser.parse_args()

    # Setup logging
    logger = get_logger("verify_runtime")
    logger.info("Starting runtime verification")

    try:
        # Load resource usage data
        resource_data = load_resource_usage(args.resource_file)
        
        # Verify runtime
        success = verify_runtime(resource_data, args.max_hours)
        
        if success:
            logger.info("Verification successful")
            sys.exit(0)
        else:
            logger.error("Verification failed")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
