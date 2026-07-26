"""
Convergence Reporter for User Story 2.

Aggregates convergence logs from individual participant model runs,
calculates the global convergence rate against the N_valid count,
and verifies/asserts it meets the >= 90% threshold (SC-002).
Generates data/models/convergence_report.json.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Import from existing project utilities
from utils.io import IOLoadError, ensure_dir, load_json, save_json
from utils.logger import get_logger

# Configuration constants
CONVERGENCE_THRESHOLD = 0.90  # SC-002: >= 90% convergence required
DEFAULT_VALID_COUNT_FILE = "data/processed/valid_participants.json"
DEFAULT_CONVERGENCE_LOGS_DIR = "data/models/convergence_logs"
DEFAULT_OUTPUT_PATH = "data/models/convergence_report.json"


class ConvergenceReportError(Exception):
    """Exception raised when convergence criteria are not met."""
    pass


def load_valid_participants(valid_count_file: str) -> List[str]:
    """
    Load the list of valid participant IDs from the runtime enforcer output.

    Args:
        valid_count_file: Path to the JSON file containing valid participant IDs.

    Returns:
        List of participant IDs.

    Raises:
        IOLoadError: If the file cannot be loaded or is malformed.
    """
    try:
        data = load_json(valid_count_file)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "participant_ids" in data:
            return data["participant_ids"]
        else:
            # Fallback: try to extract keys if it's a dict of participants
            return list(data.keys()) if isinstance(data, dict) else []
    except Exception as e:
        # If file doesn't exist or is empty, return empty list
        # This might happen if T028 hasn't run yet or failed
        if isinstance(e, FileNotFoundError):
            logging.warning(f"Valid participants file not found: {valid_count_file}. Assuming all processed participants are valid for now.")
            return []
        raise IOLoadError(f"Failed to load valid participants from {valid_count_file}: {e}")


def load_convergence_logs(logs_dir: str) -> Dict[str, Dict[str, Any]]:
    """
    Load all convergence log files from the specified directory.

    Args:
        logs_dir: Path to the directory containing convergence log JSON files.

    Returns:
        Dictionary mapping participant_id to their convergence metrics.

    Raises:
        IOLoadError: If the directory doesn't exist or logs are malformed.
    """
    logs_path = Path(logs_dir)
    if not logs_path.exists():
        raise IOLoadError(f"Convergence logs directory does not exist: {logs_dir}")

    convergence_data = {}

    for log_file in logs_path.glob("*.json"):
        try:
            participant_id = log_file.stem  # filename without extension
            data = load_json(str(log_file))

            # Validate structure
            if not isinstance(data, dict):
                logging.warning(f"Skipping malformed log file {log_file}: not a dict")
                continue

            # Ensure essential fields exist
            required_fields = ["converged", "r_hat_max", "ess_min"]
            for field in required_fields:
                if field not in data:
                    logging.warning(f"Missing field '{field}' in {log_file}, skipping")
                    continue

            convergence_data[participant_id] = data

        except Exception as e:
            logging.warning(f"Error loading log file {log_file}: {e}")
            continue

    return convergence_data


def calculate_convergence_rate(convergence_data: Dict[str, Dict[str, Any]],
                               valid_participants: List[str]) -> Tuple[float, int, int]:
    """
    Calculate the global convergence rate.

    Args:
        convergence_data: Dictionary of participant convergence metrics.
        valid_participants: List of participant IDs that passed QC.

    Returns:
        Tuple of (convergence_rate, converged_count, total_valid_count).
    """
    if not valid_participants:
        logging.warning("No valid participants found. Convergence rate is undefined.")
        return 0.0, 0, 0

    total_valid = len(valid_participants)
    converged_count = 0

    for participant_id in valid_participants:
        if participant_id in convergence_data:
            if convergence_data[participant_id].get("converged", False):
                converged_count += 1
        else:
            logging.warning(f"Participant {participant_id} has no convergence log entry")

    rate = converged_count / total_valid if total_valid > 0 else 0.0
    return rate, converged_count, total_valid


def verify_threshold(rate: float, threshold: float = CONVERGENCE_THRESHOLD) -> bool:
    """
    Verify if the convergence rate meets the required threshold.

    Args:
        rate: The calculated convergence rate.
        threshold: The minimum required rate (default 0.90).

    Returns:
        True if rate >= threshold, False otherwise.
    """
    return rate >= threshold


def generate_convergence_report(convergence_data: Dict[str, Dict[str, Any]],
                                valid_participants: List[str],
                                output_path: str) -> Dict[str, Any]:
    """
    Generate the final convergence report and save it to disk.

    Args:
        convergence_data: Dictionary of participant convergence metrics.
        valid_participants: List of participant IDs that passed QC.
        output_path: Path where the report JSON will be saved.

    Returns:
        The generated report dictionary.

    Raises:
        ConvergenceReportError: If the convergence rate is below the threshold.
    """
    rate, converged_count, total_count = calculate_convergence_rate(
        convergence_data, valid_participants
    )

    passed = verify_threshold(rate)

    # Build report structure
    report = {
        "threshold": CONVERGENCE_THRESHOLD,
        "convergence_rate": rate,
        "converged_count": converged_count,
        "total_valid_count": total_count,
        "threshold_passed": passed,
        "timestamp": None,  # Will be set by caller or system
        "participant_details": {}
    }

    # Add detailed breakdown
    for participant_id in valid_participants:
        if participant_id in convergence_data:
            details = convergence_data[participant_id]
            report["participant_details"][participant_id] = {
                "converged": details.get("converged", False),
                "r_hat_max": details.get("r_hat_max", None),
                "ess_min": details.get("ess_min", None),
                "n_samples": details.get("n_samples", None),
                "n_chains": details.get("n_chains", None)
            }
        else:
            report["participant_details"][participant_id] = {
                "converged": False,
                "error": "No convergence log found"
            }

    # Save report
    ensure_dir(output_path)
    save_json(report, output_path)

    logging.info(f"Convergence report saved to {output_path}")
    logging.info(f"Convergence Rate: {rate:.2%} ({converged_count}/{total_count})")

    if not passed:
        error_msg = (
            f"SC-002 FAILED: Convergence rate {rate:.2%} is below the required "
            f"threshold of {CONVERGENCE_THRESHOLD:.2%}. "
            f"Only {converged_count} of {total_count} valid participants converged."
        )
        logging.error(error_msg)
        raise ConvergenceReportError(error_msg)

    logging.info("SC-002 PASSED: Convergence rate meets the >= 90% threshold.")
    return report


def main():
    """
    Main entry point for the convergence reporter.

    This script:
    1. Loads the list of valid participants from T028 output.
    2. Aggregates convergence logs from T025 output.
    3. Calculates the global convergence rate.
    4. Verifies it meets the >= 90% threshold (SC-002).
    5. Generates data/models/convergence_report.json.
    """
    # Setup logging
    logger = get_logger(__name__)
    logger.setLevel(logging.INFO)

    # Parse arguments (simple override of defaults)
    import argparse
    parser = argparse.ArgumentParser(description="Generate convergence report for User Story 2")
    parser.add_argument(
        "--valid-participants",
        type=str,
        default=DEFAULT_VALID_COUNT_FILE,
        help="Path to valid participants JSON file (from T028)"
    )
    parser.add_argument(
        "--logs-dir",
        type=str,
        default=DEFAULT_CONVERGENCE_LOGS_DIR,
        help="Directory containing individual convergence logs"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_PATH,
        help="Output path for convergence report JSON"
    )
    args = parser.parse_args()

    try:
        logger.info(f"Loading valid participants from: {args.valid_participants}")
        valid_participants = load_valid_participants(args.valid_participants)
        logger.info(f"Found {len(valid_participants)} valid participants")

        logger.info(f"Loading convergence logs from: {args.logs_dir}")
        convergence_data = load_convergence_logs(args.logs_dir)
        logger.info(f"Loaded logs for {len(convergence_data)} participants")

        logger.info("Generating convergence report...")
        report = generate_convergence_report(
            convergence_data,
            valid_participants,
            args.output
        )

        logger.info("Convergence reporting completed successfully.")
        return 0

    except ConvergenceReportError as e:
        logger.error(str(e))
        # Re-raise or return non-zero to indicate failure
        # In CI/CD, this will cause the pipeline to fail as expected
        return 1
    except IOLoadError as e:
        logger.error(f"IO Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during convergence reporting: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
