"""
Run Reference-Validator Agent for T071b.
Executes validation against state/citations.yaml and writes state/validation_log.json.
Creates state/research_validated.lock if all citations are valid.
"""
import sys
import os
import json
import hashlib
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.validator import main as validate_main

def main():
    """
    Entry point for T071b: Execute Reference-Validator Agent.
    """
    # Paths relative to project root
    citations_path = project_root / "state" / "citations.yaml"
    log_path = project_root / "state" / "validation_log.json"
    lock_path = project_root / "state" / "research_validated.lock"
    research_md_path = project_root / "specs" / "001-evaluating-the-impact-of-llm-generated-c" / "research.md"

    # Verify prerequisites exist
    if not citations_path.exists():
        print(f"ERROR: Citations file not found at {citations_path}. T070a must run first.")
        sys.exit(1)

    if not research_md_path.exists():
        print(f"ERROR: Research document not found at {research_md_path}.")
        sys.exit(1)

    print(f"Starting Reference Validation for {research_md_path}...")
    
    # Run the validator logic defined in utils.validator
    # The validator expects to be called via its main() which handles the logic
    # We capture its output or re-run the logic if main() is just a CLI entry
    
    # Since utils.validator.main() is designed to run the validation pipeline:
    # It reads state/citations.yaml, fetches metadata, calculates Jaccard, writes state/validation_log.json
    try:
        validate_main()
    except Exception as e:
        print(f"Validation process failed: {e}")
        # Create a failure log to ensure the file exists for verification
        failure_log = {
            "status": "failed",
            "error": str(e),
            "timestamp": "N/A"
        }
        with open(log_path, 'w') as f:
            json.dump(failure_log, f, indent=2)
        sys.exit(1)

    # Verify the log was created
    if not log_path.exists():
        print("ERROR: Validation log was not created.")
        sys.exit(1)

    # Read the log to check status
    with open(log_path, 'r') as f:
        log_data = json.load(f)

    status = log_data.get("status", "unknown")
    
    if status == "all_valid":
        print("SUCCESS: All references validated.")
        # Create the lock file
        with open(lock_path, 'w') as f:
            f.write(f"Validated on {log_data.get('timestamp', 'unknown')}\n")
            f.write(f"Citations checked: {log_data.get('count', 0)}\n")
        print(f"Lock file created: {lock_path}")
        print("T071b PASSED: Pipeline can proceed to Phase 1.")
        return 0
    else:
        print(f"FAILURE: Validation status is '{status}'. Pipeline blocked.")
        # Do NOT create lock file
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
