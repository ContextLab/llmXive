"""Final Gate Check: Verify gate_status.json and report branching logic."""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Import shared logging utilities
from logging_config import get_logger, log_operation, log_pipeline_failure

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = DATA_DIR / "outputs"

GATE_STATUS_PATH = DATA_DIR / "gate_status.json"
STAT_GATE_STATUS_PATH = DATA_DIR / "stat_gate_status.json"
RESULTS_REPORT_PATH = PROJECT_ROOT / "results_report.md"
INSUFFICIENCY_REPORT_PATH = DATA_DIR / "data_insufficiency_report.md"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

logger = get_logger("final_gate_check")

def get_project_root() -> Path:
    return PROJECT_ROOT

def check_gate_status() -> Tuple[bool, str, Dict[str, Any]]:
    """
    Verify gate_status.json accurately reflects the Data Availability Gate outcome.

    Returns:
        Tuple[passed (bool), reason (str), status_data (dict)]
    """
    logger.log("check_gate_status", operation="check_gate_status")

    if not GATE_STATUS_PATH.exists():
        msg = f"Gate status file not found: {GATE_STATUS_PATH}"
        logger.log("gate_missing", path=str(GATE_STATUS_PATH))
        return False, msg, {}

    try:
        with open(GATE_STATUS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        msg = f"Invalid JSON in gate status: {e}"
        logger.log("gate_invalid_json", error=str(e))
        return False, msg, {}

    status = data.get("status", "").upper()
    reason = data.get("reason", "Unknown")

    if status == "PASS":
        logger.log("gate_passed", status=status, reason=reason)
        return True, "Gate passed", data
    elif status == "FAIL":
        logger.log("gate_failed", status=status, reason=reason)
        return False, reason, data
    else:
        msg = f"Unknown gate status: {status}"
        logger.log("gate_unknown_status", status=status)
        return False, msg, data

def check_report_branching(gate_passed: bool) -> Tuple[bool, str]:
    """
    Verify the pipeline branched to the correct report file based on gate status.

    Args:
        gate_passed: True if Data Availability Gate passed, False otherwise.

    Returns:
        Tuple[correct_branching (bool), message (str)]
    """
    logger.log("check_report_branching", gate_passed=gate_passed)

    if gate_passed:
        # Expect results_report.md, NOT data_insufficiency_report.md
        if RESULTS_REPORT_PATH.exists():
            # Check if it's not empty
            if RESULTS_REPORT_PATH.stat().st_size > 0:
                logger.log("branching_correct", report="results_report.md")
                return True, "Correctly generated results_report.md"
            else:
                msg = "results_report.md exists but is empty"
                logger.log("branching_empty_report", path=str(RESULTS_REPORT_PATH))
                return False, msg
        else:
            msg = "results_report.md not found after Gate Pass"
            logger.log("branching_missing_report", expected="results_report.md")
            return False, msg
    else:
        # Expect data_insufficiency_report.md, NOT results_report.md
        if INSUFFICIENCY_REPORT_PATH.exists():
            if INSUFFICIENCY_REPORT_PATH.stat().st_size > 0:
                logger.log("branching_correct", report="data_insufficiency_report.md")
                return True, "Correctly generated data_insufficiency_report.md"
            else:
                msg = "data_insufficiency_report.md exists but is empty"
                logger.log("branching_empty_insufficiency", path=str(INSUFFICIENCY_REPORT_PATH))
                return False, msg
        else:
            # Check if results_report.md was incorrectly generated
            if RESULTS_REPORT_PATH.exists():
                msg = "results_report.md found but Gate Failed (should be data_insufficiency_report.md)"
                logger.log("branching_wrong_report", found="results_report.md", expected="data_insufficiency_report.md")
                return False, msg
            else:
                msg = "data_insufficiency_report.md not found after Gate Fail"
                logger.log("branching_missing_insufficiency", expected="data_insufficiency_report.md")
                return False, msg

def main() -> int:
    """
    Main entry point for Final Gate Check.

    Returns:
        0 if check passes, 1 if check fails.
    """
    log_operation("T057_Final_Gate_Check", task="T057")

    try:
        # Step 1: Check gate_status.json
        gate_passed, gate_reason, gate_data = check_gate_status()

        if not gate_passed:
            logger.log("gate_check_failed", reason=gate_reason)
            print(f"Gate Check Failed: {gate_reason}")
            # If gate failed, we still need to check branching
            # But if gate file itself is missing or corrupt, we can't proceed
            if not gate_data:
                return 1

        # Step 2: Check report branching
        branching_correct, branching_msg = check_report_branching(gate_passed)

        if not branching_correct:
            logger.log("branching_check_failed", reason=branching_msg)
            print(f"Branching Check Failed: {branching_msg}")
            return 1

        # Step 3: Final success
        logger.log("final_gate_check_passed")
        print("Final Gate Check PASSED")
        print(f"  Gate Status: {'PASS' if gate_passed else 'FAIL'}")
        print(f"  Report Branching: Correct")

        return 0

    except Exception as e:
        log_pipeline_failure("T057_Final_Gate_Check", str(e))
        logger.log("exception", error=str(e))
        print(f"Final Gate Check FAILED with exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())