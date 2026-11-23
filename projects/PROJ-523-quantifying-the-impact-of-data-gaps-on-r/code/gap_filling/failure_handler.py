"""
Failure Handler Module for Gap Filling Analysis.

This module implements FR-008: Convergence failure handling.
It provides mechanisms to log convergence failures, record the specific
gap configuration that caused the failure, and exclude these realizations
from downstream analysis.
"""

import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

# Import project constants and paths from config
try:
    from config import DATA_DERIVED_DIR, DATA_RESULTS_DIR
except ImportError:
    # Fallback for standalone execution or different project root structure
    DATA_DERIVED_DIR = Path("data/derived")
    DATA_RESULTS_DIR = Path("data/results")

# Ensure the failure log directory exists
FAILURE_LOG_DIR = DATA_DERIVED_DIR / "failure_logs"

logger = logging.getLogger(__name__)

def ensure_failure_log_dir():
    """Create the failure log directory if it does not exist."""
    if not FAILURE_LOG_DIR.exists():
        logger.info(f"Creating failure log directory: {FAILURE_LOG_DIR}")
        FAILURE_LOG_DIR.mkdir(parents=True, exist_ok=True)
    return FAILURE_LOG_DIR

def log_convergence_failure(
    realization_id: str,
    algo_name: str,
    gap_fraction: float,
    gap_morphology: str,
    error_message: str,
    timestamp: Optional[str] = None
) -> str:
    """
    Log a convergence failure to a JSON file.

    Args:
        realization_id: Unique identifier for the realization.
        algo_name: Name of the algorithm that failed.
        gap_fraction: The gap fraction used in this realization.
        gap_morphology: The morphology type of the gap mask.
        error_message: The specific error message or exception string.
        timestamp: Optional ISO format timestamp. Defaults to now.

    Returns:
        The path to the log file where this failure was recorded.
    """
    ensure_failure_log_dir()
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()

    failure_entry = {
        "realization_id": realization_id,
        "algorithm": algo_name,
        "gap_config": {
            "fraction": gap_fraction,
            "morphology": gap_morphology
        },
        "error": error_message,
        "timestamp": timestamp
    }

    # Append to a central log file for this realization/algorithm combo
    # or a global failure log. Let's use a global failure log for the run.
    failure_log_path = FAILURE_LOG_DIR / "convergence_failures.json"

    # Load existing failures if any
    existing_failures = []
    if failure_log_path.exists():
        try:
            with open(failure_log_path, 'r') as f:
                existing_failures = json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Corrupted failure log at {failure_log_path}, starting fresh.")
            existing_failures = []

    existing_failures.append(failure_entry)

    with open(failure_log_path, 'w') as f:
        json.dump(existing_failures, f, indent=2)

    logger.error(f"Convergence failure logged: {realization_id} - {algo_name}: {error_message}")
    return str(failure_log_path)

def record_excluded_realization(
    realization_id: str,
    reason: str = "convergence_failure",
    timestamp: Optional[str] = None
):
    """
    Record a realization ID to the exclusion list.

    Args:
        realization_id: The ID of the realization to exclude.
        reason: The reason for exclusion (default: convergence_failure).
        timestamp: Optional ISO format timestamp.
    """
    ensure_failure_log_dir()
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()

    exclusion_entry = {
        "realization_id": realization_id,
        "reason": reason,
        "timestamp": timestamp
    }

    exclusion_log_path = FAILURE_LOG_DIR / "excluded_realizations.json"

    existing_exclusions = []
    if exclusion_log_path.exists():
        try:
            with open(exclusion_log_path, 'r') as f:
                existing_exclusions = json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Corrupted exclusion log at {exclusion_log_path}, starting fresh.")
            existing_exclusions = []

    existing_exclusions.append(exclusion_entry)

    with open(exclusion_log_path, 'w') as f:
        json.dump(existing_exclusions, f, indent=2)

    logger.warning(f"Realization {realization_id} marked as excluded: {reason}")

def handle_convergence_failure(
    realization_id: str,
    algo_name: str,
    gap_fraction: float,
    gap_morphology: str,
    exception: Exception
):
    """
    Central handler for convergence failures.
    1. Logs the specific failure details.
    2. Records the realization as excluded.
    3. Returns a flag indicating the failure was handled (for pipeline control).

    Args:
        realization_id: ID of the realization.
        algo_name: Algorithm name.
        gap_fraction: Gap fraction.
        gap_morphology: Gap morphology.
        exception: The caught exception object.

    Returns:
        bool: Always True, indicating the failure was handled and logged.
    """
    error_msg = f"{type(exception).__name__}: {str(exception)}"
    
    # Log the detailed failure
    log_convergence_failure(
        realization_id=realization_id,
        algo_name=algo_name,
        gap_fraction=gap_fraction,
        gap_morphology=gap_morphology,
        error_message=error_msg
    )

    # Record as excluded
    record_excluded_realization(
        realization_id=realization_id,
        reason=f"convergence_failure_{algo_name}"
    )

    return True

def get_excluded_realization_ids() -> Set[str]:
    """
    Load all excluded realization IDs from the exclusion log.

    Returns:
        A set of realization IDs that have been excluded.
    """
    exclusion_log_path = FAILURE_LOG_DIR / "excluded_realizations.json"
    if not exclusion_log_path.exists():
        return set()

    try:
        with open(exclusion_log_path, 'r') as f:
            data = json.load(f)
        return {entry["realization_id"] for entry in data}
    except (json.JSONDecodeError, KeyError):
        logger.error("Could not parse excluded realizations log.")
        return set()

def is_realization_excluded(realization_id: str) -> bool:
    """
    Check if a specific realization ID is in the exclusion list.

    Args:
        realization_id: The ID to check.

    Returns:
        True if excluded, False otherwise.
    """
    excluded_ids = get_excluded_realization_ids()
    return realization_id in excluded_ids

def run_failure_handler_pipeline():
    """
    Standalone entry point to run the failure handler pipeline.
    Currently, this is a placeholder as the logic is integrated into
    the main analysis loop. It ensures directories are ready.
    """
    ensure_failure_log_dir()
    logger.info("Failure handler pipeline initialized.")
    return True

def main():
    """Main entry point for CLI execution."""
    logging.basicConfig(level=logging.INFO)
    run_failure_handler_pipeline()

if __name__ == "__main__":
    main()
