"""
Convergence failure handling module for gap-filling algorithms.

Implements FR-008: Add convergence failure handling: log failure, record gap config,
exclude from analysis.
"""
import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import yaml

# Import from existing project modules
from config import (
    DATA_DERIVED_DIR,
    DATA_RESULTS_DIR,
    N_SIDE,
    GAP_FRACTIONS,
    GAP_MORPHOLOGIES,
    get_dtype
)
from data_io import save_metadata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
FAILURE_LOG_FILE = "data/results/convergence_failures.json"
EXCLUDED_REALIZATIONS_FILE = "data/results/excluded_realizations.csv"


def ensure_failure_log_dir():
    """Ensure the directory for failure logs exists."""
    failure_dir = Path(FAILURE_LOG_FILE).parent
    failure_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured failure log directory exists: {failure_dir}")


def log_convergence_failure(
    realization_id: str,
    algo_name: str,
    gap_fraction: float,
    gap_morphology: str,
    error_message: str,
    exec_time_sec: float,
    stack_trace: Optional[str] = None
) -> Dict[str, Any]:
    """
    Log a convergence failure with full context.
    
    Args:
        realization_id: Unique identifier for the realization
        algo_name: Name of the algorithm that failed
        gap_fraction: Target gap fraction
        gap_morphology: Type of gap morphology
        error_message: Error message from the exception
        exec_time_sec: Execution time before failure
        stack_trace: Optional full stack trace string
    
    Returns:
        Dictionary containing the failure record
    """
    ensure_failure_log_dir()
    
    failure_record = {
        "timestamp": datetime.utcnow().isoformat(),
        "realization_id": realization_id,
        "algorithm": {
            "name": algo_name,
            "version": "unknown"  # Could be extended to get actual version
        },
        "gap_configuration": {
            "fraction": gap_fraction,
            "morphology": gap_morphology
        },
        "error": {
            "message": error_message,
            "stack_trace": stack_trace
        },
        "execution_time_sec": exec_time_sec,
        "status": "CONVERGENCE_FAILURE"
    }
    
    # Load existing failures if any
    failure_log_path = Path(FAILURE_LOG_FILE)
    if failure_log_path.exists():
        with open(failure_log_path, 'r') as f:
            existing_log = json.load(f)
    else:
        existing_log = {"failures": []}
    
    # Append new failure
    existing_log["failures"].append(failure_record)
    
    # Save updated log
    with open(failure_log_path, 'w') as f:
        json.dump(existing_log, f, indent=2)
    
    logger.warning(
        f"Convergence failure logged: realization={realization_id}, "
        f"algo={algo_name}, gap={gap_fraction}%, morphology={gap_morphology}"
    )
    
    return failure_record


def record_excluded_realization(
    realization_id: str,
    algo_name: str,
    gap_fraction: float,
    gap_morphology: str,
    reason: str = "CONVERGENCE_FAILURE"
):
    """
    Record an excluded realization to the CSV file for downstream filtering.
    
    Args:
        realization_id: Unique identifier for the realization
        algo_name: Name of the algorithm
        gap_fraction: Target gap fraction
        gap_morphology: Type of gap morphology
        reason: Reason for exclusion (default: CONVERGENCE_FAILURE)
    """
    ensure_failure_log_dir()
    
    fieldnames = [
        "realization_id",
        "algorithm",
        "gap_fraction",
        "gap_morphology",
        "reason",
        "excluded_at"
    ]
    
    csv_path = Path(EXCLUDED_REALIZATIONS_FILE)
    
    # Check if file exists to determine if we need headers
    file_exists = csv_path.exists()
    
    with open(csv_path, 'a', newline='') as f:
        import csv
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            "realization_id": realization_id,
            "algorithm": algo_name,
            "gap_fraction": gap_fraction,
            "gap_morphology": gap_morphology,
            "reason": reason,
            "excluded_at": datetime.utcnow().isoformat()
        })
    
    logger.info(
        f"Excluded realization recorded: {realization_id} ({algo_name}) - {reason}"
    )


def handle_convergence_failure(
    exception: Exception,
    realization_id: str,
    algo_name: str,
    gap_fraction: float,
    gap_morphology: str,
    exec_time_sec: float
) -> Dict[str, Any]:
    """
    Central handler for convergence failures.
    
    This function:
    1. Logs the failure with full context
    2. Records the exclusion
    3. Returns a status dict for the calling code
    
    Args:
        exception: The exception that was raised
        realization_id: Unique identifier for the realization
        algo_name: Name of the algorithm
        gap_fraction: Target gap fraction
        gap_morphology: Type of gap morphology
        exec_time_sec: Execution time before failure
    
    Returns:
        Dictionary with status information for the caller
    """
    import traceback
    
    # Get full stack trace
    stack_trace = traceback.format_exc()
    
    # Log the failure
    failure_record = log_convergence_failure(
        realization_id=realization_id,
        algo_name=algo_name,
        gap_fraction=gap_fraction,
        gap_morphology=gap_morphology,
        error_message=str(exception),
        exec_time_sec=exec_time_sec,
        stack_trace=stack_trace
    )
    
    # Record exclusion
    record_excluded_realization(
        realization_id=realization_id,
        algo_name=algo_name,
        gap_fraction=gap_fraction,
        gap_morphology=gap_morphology,
        reason="CONVERGENCE_FAILURE"
    )
    
    return {
        "status": "EXCLUDED",
        "realization_id": realization_id,
        "algorithm": algo_name,
        "reason": "CONVERGENCE_FAILURE",
        "failure_record": failure_record
    }


def get_excluded_realization_ids() -> List[str]:
    """
    Load list of excluded realization IDs from the CSV file.
    
    Returns:
        List of realization IDs that should be excluded from analysis
    """
    excluded_ids = []
    csv_path = Path(EXCLUDED_REALIZATIONS_FILE)
    
    if not csv_path.exists():
        logger.debug("No excluded realizations file found")
        return excluded_ids
    
    import csv
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            excluded_ids.append(row['realization_id'])
    
    logger.info(f"Loaded {len(excluded_ids)} excluded realization IDs")
    return excluded_ids


def is_realization_excluded(realization_id: str) -> bool:
    """
    Check if a realization ID is in the excluded list.
    
    Args:
        realization_id: The ID to check
    
    Returns:
        True if excluded, False otherwise
    """
    excluded_ids = get_excluded_realization_ids()
    return realization_id in excluded_ids


def run_failure_handler_pipeline():
    """
    Main entry point for the failure handler pipeline.
    
    This function can be called to:
    1. Initialize the failure logging infrastructure
    2. Provide a summary of current failures
    """
    ensure_failure_log_dir()
    
    failure_log_path = Path(FAILURE_LOG_FILE)
    excluded_path = Path(EXCLUDED_REALIZATIONS_FILE)
    
    summary = {
        "failure_log_exists": failure_log_path.exists(),
        "excluded_csv_exists": excluded_path.exists(),
        "total_failures": 0,
        "excluded_count": 0
    }
    
    if failure_log_path.exists():
        with open(failure_log_path, 'r') as f:
            log_data = json.load(f)
            summary["total_failures"] = len(log_data.get("failures", []))
    
    if excluded_path.exists():
        import csv
        with open(excluded_path, 'r') as f:
            reader = csv.DictReader(f)
            summary["excluded_count"] = sum(1 for _ in reader)
    
    logger.info(f"Failure handler pipeline summary: {summary}")
    return summary


def main():
    """Command-line entry point for testing the failure handler."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test the failure handler
        logger.info("Running failure handler test...")
        
        # Simulate a failure
        result = handle_convergence_failure(
            exception=Exception("Test convergence failure"),
            realization_id="test_001",
            algo_name="harmonic_interpolation",
            gap_fraction=0.15,
            gap_morphology="clustered",
            exec_time_sec=12.5
        )
        
        logger.info(f"Test result: {result}")
        
        # Verify exclusion
        is_excluded = is_realization_excluded("test_001")
        logger.info(f"Is test_001 excluded? {is_excluded}")
        
        # Run pipeline summary
        summary = run_failure_handler_pipeline()
        logger.info(f"Pipeline summary: {summary}")
        
        print("Failure handler test completed successfully")
        return 0
    
    else:
        # Normal operation - just initialize
        run_failure_handler_pipeline()
        print("Failure handler initialized. Use --test to run self-test.")
        return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
