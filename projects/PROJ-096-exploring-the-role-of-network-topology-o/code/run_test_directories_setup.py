"""
Script to execute the test directory creation and verify the results.
This script is run to satisfy the "real outputs" requirement for T001c.
It creates the directories and writes a verification report.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(code_dir))

from setup_test_directories import create_test_directories

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    project_root = code_dir.parent
    logging.info(f"Project root: {project_root}")

    # Create directories
    success = create_test_directories()

    if not success:
        logging.error("Directory creation failed.")
        return 1

    # Verify directories exist
    tests_dir = project_root / "tests"
    state_projects_dir = project_root / "state" / "projects"

    verification_report = {
        "task_id": "T001c",
        "status": "success" if success else "failed",
        "directories": {
            "tests": {
                "path": str(tests_dir),
                "exists": tests_dir.exists(),
                "is_dir": tests_dir.is_dir()
            },
            "state_projects": {
                "path": str(state_projects_dir),
                "exists": state_projects_dir.exists(),
                "is_dir": state_projects_dir.is_dir()
            }
        }
    }

    # Write verification report
    report_path = project_root / "data" / "processed" / "test_directories_verification.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w') as f:
        json.dump(verification_report, f, indent=2)

    logging.info(f"Verification report written to: {report_path}")

    if not (tests_dir.exists() and state_projects_dir.exists()):
        logging.error("Verification failed: One or more directories do not exist.")
        return 1

    logging.info("All directories verified successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())