"""
Instrumentation Validator for User Story 1 (T014d).

This module handles SC-006 variable fit validation for instrumentation data.
It validates raw metrics from T014a (instrumentor_remote.py) and updates
data/raw/validation_status.json with critical/non-critical missing terms.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from orchestrator.logger import get_logger

# Constants for file paths
RAW_DIR = Path("code/data/raw")
VALIDATION_STATUS_FILE = RAW_DIR / "validation_status.json"

logger = get_logger(__name__)

class InstrumentationValidationError(Exception):
    """Raised when instrumentation validation fails critically."""
    pass


def load_validation_status() -> Dict[str, Any]:
    """
    Load the existing validation status file or return a fresh structure.
    """
    if VALIDATION_STATUS_FILE.exists():
        try:
            with open(VALIDATION_STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not read existing validation_status.json: {e}. Starting fresh.")
            return {
                "critical_missing": [],
                "non_critical_missing": [],
                "excluded_terms": [],
                "warnings": [],
                "status": "valid",
                "reduced_model_config": {}
            }
    else:
        # Ensure directory exists
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        return {
            "critical_missing": [],
            "non_critical_missing": [],
            "excluded_terms": [],
            "warnings": [],
            "status": "valid",
            "reduced_model_config": {}
        }


def save_validation_status(status_data: Dict[str, Any]) -> None:
    """
    Save the validation status to disk.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(VALIDATION_STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, indent=2)
    logger.info(f"Updated validation status saved to {VALIDATION_STATUS_FILE}")


def validate_instrumentation_data(raw_metrics_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate instrumentation data from T014a.

    Specifics:
    - Input: Raw metrics from T014a (packet_count, cpu_utilization_pct).
    - Logic:
      - If cpu_utilization_pct is missing or flagged as error by T014a:
        - Flag the run as 'WARN' or 'EXCLUDED' in validation_status.json.
        - Do NOT proceed with zero-filled data.
      - If packet_count is missing or -1 (uninstrumented):
        - Flag as non-critical missing (WARNING).
    - Output: Update data/raw/validation_status.json with critical_missing or excluded_terms.

    Args:
        raw_metrics_path: Optional path to a specific raw metrics JSON file.
                          If None, looks for the latest run or scans directory.
    """
    status_data = load_validation_status()

    # Determine which metrics to check.
    # If a specific path is provided, load it. Otherwise, we check the general status
    # based on the assumption that T014a has already written its findings to a raw file
    # or that we are validating the run context.
    # For T014d, we specifically validate the *fit* of the variables.
    # We assume the data_collector (T017) or T014a itself has produced a raw JSON
    # or CSV. Since T014a outputs dicts, we look for the aggregated raw data.

    # Strategy: Check for the existence of a specific "latest" raw metrics file
    # or iterate through raw files to find instrumentation errors.
    # However, the spec says "Input: Raw metrics from T014a".
    # T014a writes to data/raw/... (implied). Let's check for a generic raw file
    # or the validation_status itself if T014a already wrote to it.

    # Since T014a is the source of truth for "InstrumentationError",
    # we assume T014a might have already flagged it, OR we check the raw data
    # if available.
    # To be robust, we will check for a file named 'instrumentation_raw.json'
    # or similar in the raw directory, or simply update the status based on
    # the *absence* of expected columns if we were reading a CSV.
    # But the spec says "Input: Raw metrics from T014a".
    # Let's assume T014a produces a file like `code/data/raw/instrumentation_metrics.json`
    # or similar. If not found, we assume the run is valid unless we find errors.

    # Actually, the most reliable way per T014a spec: T014a raises InstrumentationError
    # or logs WARNING. T014d's job is to read the *result* of that run.
    # If T014a failed, it likely didn't produce data.
    # If T014a produced partial data (cpu_utilization_pct = null), we must flag it.

    # Let's scan for the latest raw data file that might contain these metrics.
    # T017 produces a CSV, but T014d runs before T017?
    # Dependency says: T014d depends on T014a. T017 depends on T014a.
    # T010a depends on T017.
    # So T014d runs *after* T014a but *before* T017? Or concurrently?
    # "Dependency: T014a".
    # We will check for a file generated by T014a.
    # Let's assume T014a writes to `code/data/raw/instrumentation_raw.json` if successful,
    # or we check the validation status if T014a already updated it.

    # To be safe and strictly follow "Input: Raw metrics from T014a",
    # we will look for a file named `instrumentation_metrics.json` in the raw dir.
    # If it doesn't exist, we assume T014a hasn't run or failed silently (which shouldn't happen).
    # If it exists, we check for null/missing values.

    instrumentation_file = RAW_DIR / "instrumentation_metrics.json"
    metrics_data = None

    if instrumentation_file.exists():
        try:
            with open(instrumentation_file, 'r', encoding='utf-8') as f:
                metrics_data = json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in {instrumentation_file}")
            status_data["warnings"].append(f"Invalid JSON in {instrumentation_file}")
            status_data["status"] = "WARN"
    else:
        # Fallback: Check if T014a wrote to a generic raw file or if we should just
        # assume the run is valid if no file exists (maybe T014a hasn't run yet).
        # But T014d depends on T014a, so we expect data.
        logger.warning(f"No instrumentation metrics found at {instrumentation_file}. "
                       "Assuming T014a has not produced data or failed. "
                       "Flagging as potential missing critical data.")
        # If T014a is a prerequisite, and no file exists, it implies failure.
        status_data["critical_missing"].append("instrumentation_raw_data")
        status_data["status"] = "excluded"
        save_validation_status(status_data)
        return status_data

    if metrics_data:
        # Check for critical variable: cpu_utilization_pct
        # T014a spec: "If mpstat is missing... set cpu_utilization_pct to null... flag run as WARN"
        # T014d spec: "If cpu_utilization_pct is missing or flagged as error... flag run as WARN or EXCLUDED"

        cpu_util = metrics_data.get("cpu_utilization_pct")

        if cpu_util is None:
            logger.warning("cpu_utilization_pct is missing or null. Flagging as non-critical missing.")
            if "cpu_utilization_pct" not in status_data["non_critical_missing"]:
                status_data["non_critical_missing"].append("cpu_utilization_pct")
            # Update reduced_model_config
            if "excluded_terms" not in status_data:
                status_data["excluded_terms"] = []
            status_data["excluded_terms"].append("cpu_utilization_pct")
            if status_data["status"] != "excluded":
                status_data["status"] = "WARN"

        # Check for critical variable: packet_count (if uninstrumented)
        # T014a spec: "If tcpdump is missing... raise InstrumentationError immediately"
        # If we are here, tcpdump likely worked. But check for -1 (uninstrumented).
        packet_count = metrics_data.get("packet_count")
        if packet_count == -1:
            logger.warning("packet_count is -1 (uninstrumented). Flagging as non-critical missing.")
            if "packet_count" not in status_data["non_critical_missing"]:
                status_data["non_critical_missing"].append("packet_count")
            if "excluded_terms" not in status_data:
                status_data["excluded_terms"] = []
            status_data["excluded_terms"].append("packet_count")
            if status_data["status"] != "excluded":
                status_data["status"] = "WARN"

        # Check for any explicit error flags from T014a
        if metrics_data.get("error"):
            error_msg = metrics_data.get("error")
            logger.error(f"Instrumentation error detected: {error_msg}")
            status_data["critical_missing"].append("instrumentation_error")
            status_data["status"] = "excluded"

    save_validation_status(status_data)
    return status_data


def main():
    """
    Entry point for the instrumentation validator.
    """
    logger.info("Starting instrumentation validation (T014d)...")
    result = validate_instrumentation_data()
    logger.info(f"Validation complete. Status: {result['status']}")
    logger.info(f"Critical missing: {result['critical_missing']}")
    logger.info(f"Non-critical missing: {result['non_critical_missing']}")
    logger.info(f"Excluded terms: {result['excluded_terms']}")


if __name__ == "__main__":
    main()