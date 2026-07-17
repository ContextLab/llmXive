"""
Gate verification for Constitution II (Verified Accuracy) compliance.

This module ensures that prerequisite tasks T038 and T042 are completed
and that the verification report indicates success before allowing
final report generation (T032).
"""
import os
import sys
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
VERIFICATION_REPORT_PATH = DATA_DIR / "verification_report.json"
DOWNLOAD_ERRORS_LOG = DATA_DIR / "download_errors.log"
GATE_STATUS_PATH = DATA_DIR / "constitution_gate_status.json"

# Prerequisite tasks
PREREQ_TASKS = ["T038", "T042"]

def check_prerequisite_task_completed(task_id: str) -> bool:
    """
    Check if a prerequisite task is marked as completed in the tasks.md file.
    
    Args:
        task_id: The task ID to check (e.g., "T038")
        
    Returns:
        True if the task is marked as completed, False otherwise.
    """
    tasks_md_path = PROJECT_ROOT / "tasks.md"
    
    if not tasks_md_path.exists():
        logger.error(f"tasks.md not found at {tasks_md_path}")
        return False
    
    try:
        with open(tasks_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for the task line with [X] (completed)
        # Format: - [X] T044 ...
        task_line = f"- [X] {task_id}"
        
        if task_line in content:
            logger.info(f"Task {task_id} is marked as completed in tasks.md")
            return True
        else:
            logger.warning(f"Task {task_id} is NOT marked as completed in tasks.md")
            return False
    except Exception as e:
        logger.error(f"Error reading tasks.md: {e}")
        return False

def verify_verification_report() -> dict:
    """
    Verify that the verification report exists and indicates success.
    
    Returns:
        A dictionary containing the verification result and details.
    """
    result = {
        "status": "failed",
        "report_exists": False,
        "report_valid": False,
        "report_status": None,
        "errors": []
    }
    
    if not VERIFICATION_REPORT_PATH.exists():
        result["errors"].append(f"Verification report not found at {VERIFICATION_REPORT_PATH}")
        logger.error(f"Verification report not found at {VERIFICATION_REPORT_PATH}")
        return result
    
    result["report_exists"] = True
    
    try:
        with open(VERIFICATION_REPORT_PATH, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        result["report_valid"] = True
        result["report_status"] = report_data.get("status")
        
        if report_data.get("status") == "SUCCESS":
            result["status"] = "success"
            logger.info("Verification report indicates SUCCESS")
        else:
            result["status"] = "failed"
            result["errors"].append(f"Verification report status is '{report_data.get('status')}', expected 'SUCCESS'")
            logger.warning(f"Verification report status is '{report_data.get('status')}'")
            
    except json.JSONDecodeError as e:
        result["report_valid"] = False
        result["errors"].append(f"Invalid JSON in verification report: {e}")
        logger.error(f"Invalid JSON in verification report: {e}")
    except Exception as e:
        result["errors"].append(f"Error reading verification report: {e}")
        logger.error(f"Error reading verification report: {e}")
    
    return result

def check_download_errors_log() -> dict:
    """
    Check if there are any errors in the download errors log.
    
    Returns:
        A dictionary containing the check result and details.
    """
    result = {
        "status": "success",
        "log_exists": False,
        "has_errors": False,
        "errors": []
    }
    
    if not DOWNLOAD_ERRORS_LOG.exists():
        logger.info("Download errors log does not exist (no errors recorded)")
        result["log_exists"] = False
        return result
    
    result["log_exists"] = True
    
    try:
        with open(DOWNLOAD_ERRORS_LOG, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if content.strip():
            result["has_errors"] = True
            result["status"] = "failed"
            error_lines = [line for line in content.strip().split('\n') if line.strip()]
            result["errors"].extend(error_lines[:10])  # Limit to first 10 errors
            logger.warning(f"Found {len(error_lines)} errors in download log")
        else:
            logger.info("Download errors log exists but is empty")
            
    except Exception as e:
        result["errors"].append(f"Error reading download errors log: {e}")
        logger.error(f"Error reading download errors log: {e}")
    
    return result

def main():
    """
    Main function to verify Constitution II compliance.
    
    This function:
    1. Checks if prerequisite tasks T038 and T042 are completed
    2. Verifies the verification report exists and indicates success
    3. Checks the download errors log for any issues
    4. Generates a gate status report
    5. Returns exit code 0 if gate passes, 1 otherwise
    """
    logger.info("Starting Constitution II compliance verification...")
    
    all_checks_passed = True
    gate_result = {
        "gate_passed": False,
        "prerequisite_tasks": {},
        "verification_report": {},
        "download_errors": {},
        "timestamp": None,
        "errors": []
    }
    
    # Check prerequisite tasks
    logger.info("Checking prerequisite tasks...")
    for task_id in PREREQ_TASKS:
        task_completed = check_prerequisite_task_completed(task_id)
        gate_result["prerequisite_tasks"][task_id] = task_completed
        if not task_completed:
            all_checks_passed = False
            gate_result["errors"].append(f"Prerequisite task {task_id} is not completed")
    
    # Verify verification report
    logger.info("Verifying verification report...")
    verification_result = verify_verification_report()
    gate_result["verification_report"] = verification_result
    if verification_result["status"] != "success":
        all_checks_passed = False
        gate_result["errors"].extend(verification_result["errors"])
    
    # Check download errors log
    logger.info("Checking download errors log...")
    download_errors_result = check_download_errors_log()
    gate_result["download_errors"] = download_errors_result
    if download_errors_result["status"] != "success":
        all_checks_passed = False
        gate_result["errors"].extend(download_errors_result["errors"])
    
    # Set timestamp
    import datetime
    gate_result["timestamp"] = datetime.datetime.now().isoformat()
    
    # Set final gate status
    gate_result["gate_passed"] = all_checks_passed
    
    # Save gate status report
    try:
        with open(GATE_STATUS_PATH, 'w', encoding='utf-8') as f:
            json.dump(gate_result, f, indent=2)
        logger.info(f"Gate status report saved to {GATE_STATUS_PATH}")
    except Exception as e:
        logger.error(f"Failed to save gate status report: {e}")
    
    # Log final result
    if all_checks_passed:
        logger.info("✅ Constitution II compliance check PASSED")
        print("GATE_PASSED")
        return 0
    else:
        logger.error("❌ Constitution II compliance check FAILED")
        print("GATE_FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
