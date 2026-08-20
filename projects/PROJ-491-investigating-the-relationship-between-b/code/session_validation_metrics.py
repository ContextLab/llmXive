"""
Module to calculate and report session validation metrics.
Implements T013b: Calculate pass-rate percentage and write to JSON.
"""
import os
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

from config import ensure_directories
from write_excluded_session_ids import load_validation_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_pass_rate(valid_count: int, total_count: int) -> float:
    """
    Calculate the pass-rate percentage of subjects with distinct session IDs.

    Args:
        valid_count: Number of subjects with valid (distinct) session IDs.
        total_count: Total number of subjects attempted.

    Returns:
        Pass rate as a percentage (0.0 to 100.0).
    """
    if total_count == 0:
        return 0.0
    return (valid_count / total_count) * 100.0

def write_metrics(metrics: Dict[str, Any], output_path: Path) -> None:
    """
    Write the validation metrics to a JSON file.

    Args:
        metrics: Dictionary containing the metrics to write.
        output_path: Path to the output JSON file.
    """
    # Ensure directory exists
    ensure_directories([output_path.parent])

    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Metrics written to {output_path}")

def main() -> int:
    """
    Main entry point for calculating and writing session validation metrics.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        # Load validation state from the previous step (T013)
        validation_data = load_validation_state()

        if validation_data is None:
            logger.error("No validation state found. Did T013 run successfully?")
            return 1

        total_subjects = validation_data.get('total_subjects', 0)
        valid_subjects = validation_data.get('valid_subjects', 0)
        excluded_subjects = validation_data.get('excluded_subjects', [])

        if total_subjects == 0:
            logger.warning("Total subjects is 0. Cannot calculate pass rate.")
            pass_rate = 0.0
        else:
            pass_rate = calculate_pass_rate(valid_subjects, total_subjects)

        metrics = {
            "total_subjects": total_subjects,
            "valid_subjects": valid_subjects,
            "excluded_subjects_count": len(excluded_subjects),
            "pass_rate_percentage": round(pass_rate, 2),
            "validation_status": "passed" if pass_rate == 100.0 else "partial" if valid_subjects > 0 else "failed"
        }

        output_path = Path("data/processed/session_validation_metrics.json")
        write_metrics(metrics, output_path)

        logger.info(f"Session validation complete. Pass rate: {pass_rate:.2f}%")
        return 0

    except Exception as e:
        logger.error(f"Error calculating metrics: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
