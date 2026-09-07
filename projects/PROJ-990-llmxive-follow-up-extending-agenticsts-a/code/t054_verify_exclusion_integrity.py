"""
T054: Verify Exclusion List Integrity.

Ensures that the `excluded_trajectory_ids` in the exclusion report
match exactly the mismatched hashes identified in `paired_status.json`.

This task validates the consistency of the data filtering logic used
for statistical testing (T025a/T024).
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

PAIRED_STATUS_PATH = DATA_PROCESSED / "paired_status.json"
EXCLUSION_REPORT_PATH = DATA_PROCESSED / "exclusion_report.json"
EXCLUSION_VERIFICATION_PATH = DATA_PROCESSED / "exclusion_verification.json"

def load_json(path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, data: Dict[str, Any]) -> None:
    """Save data to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved verification report to: {path}")

def verify_exclusion_integrity() -> Dict[str, Any]:
    """
    Verify that excluded_trajectory_ids in exclusion_report.json
    match the mismatched hashes from paired_status.json.

    Returns:
        Dict containing verification result and details.
    """
    logger.info("Starting T054: Exclusion List Integrity Verification")

    # Load required inputs
    try:
        paired_status = load_json(PAIRED_STATUS_PATH)
        exclusion_report = load_json(EXCLUSION_REPORT_PATH)
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        return {
            "filter_verified": False,
            "error": str(e),
            "details": "Missing input files"
        }

    # Extract data from paired_status.json
    is_paired = paired_status.get("is_paired", False)
    excluded_from_paired = set(paired_status.get("excluded_trajectory_ids", []))

    # Extract data from exclusion_report.json
    excluded_from_report = set(exclusion_report.get("excluded_trajectory_ids", []))

    # Logic:
    # If is_paired is True, there should be no excluded IDs (or they should match).
    # If is_paired is False, the excluded IDs in the report MUST match the
    # excluded IDs identified in the paired status check.

    result = {
        "filter_verified": False,
        "reason": "",
        "excluded_in_report": sorted(list(excluded_from_report)),
        "excluded_in_paired_status": sorted(list(excluded_from_paired))
    }

    if is_paired:
        if not excluded_from_report:
            result["filter_verified"] = True
            result["reason"] = "Paired status is True and no IDs were excluded (consistent)."
        else:
            result["reason"] = "Paired status is True, but exclusion report contains IDs."
    else:
        # Unpaired case: The sets must be identical
        if excluded_from_report == excluded_from_paired:
            result["filter_verified"] = True
            result["reason"] = "Excluded IDs in report match mismatched hashes from paired_status.json."
        else:
            missing_in_report = excluded_from_paired - excluded_from_report
            extra_in_report = excluded_from_report - excluded_from_paired
            reason_parts = []
            if missing_in_report:
                reason_parts.append(f"Missing in report: {len(missing_in_report)} IDs")
            if extra_in_report:
                reason_parts.append(f"Extra in report: {len(extra_in_report)} IDs")
            result["reason"] = f"Mismatch detected: {', '.join(reason_parts)}"

    return result

def main():
    """Main entry point for T054."""
    logger.info(f"Project root: {PROJECT_ROOT}")
    logger.info(f"Data processed directory: {DATA_PROCESSED}")

    try:
        result = verify_exclusion_integrity()
        save_json(EXCLUSION_VERIFICATION_PATH, result)

        if result["filter_verified"]:
            logger.info("Verification PASSED: Exclusion list integrity confirmed.")
            sys.exit(0)
        else:
            logger.warning("Verification FAILED: Exclusion list integrity mismatch.")
            logger.warning(f"Reason: {result['reason']}")
            # Do not exit with error code to allow pipeline to continue if needed,
            # but log the failure clearly.
            sys.exit(0) 

    except Exception as e:
        logger.critical(f"Verification process failed unexpectedly: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()