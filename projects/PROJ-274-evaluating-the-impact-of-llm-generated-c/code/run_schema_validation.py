"""
Task T033: Run schema validation on participant logs.

This script validates data/raw/participant_logs.json against contracts/dataset.schema.yaml.
It acts as a gate: if validation fails, it writes a failure report and exits with code 1.
If validation passes, it writes a success report and exits with code 0.

Output: data/processed/validation_report.json
"""

import json
import os
import sys
import yaml
from datetime import datetime

# Import from existing API surface
from validation import run_schema_validation, save_validation_report

# Paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_LOGS_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "participant_logs.json")
SCHEMA_PATH = os.path.join(PROJECT_ROOT, "contracts", "dataset.schema.yaml")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "validation_report.json")

def main():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Check prerequisites
    if not os.path.exists(RAW_LOGS_PATH):
        error_msg = f"Raw logs file not found: {RAW_LOGS_PATH}"
        print(f"ERROR: {error_msg}", file=sys.stderr)
        report = {
            "status": "failed",
            "reason": "Input file missing",
            "input_path": RAW_LOGS_PATH,
            "timestamp": datetime.utcnow().isoformat()
        }
        save_validation_report(report, OUTPUT_PATH)
        sys.exit(1)

    if not os.path.exists(SCHEMA_PATH):
        error_msg = f"Schema file not found: {SCHEMA_PATH}"
        print(f"ERROR: {error_msg}", file=sys.stderr)
        report = {
            "status": "failed",
            "reason": "Schema file missing",
            "schema_path": SCHEMA_PATH,
            "timestamp": datetime.utcnow().isoformat()
        }
        save_validation_report(report, OUTPUT_PATH)
        sys.exit(1)

    # Load schema
    try:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
    except Exception as e:
        error_msg = f"Failed to load schema: {e}"
        print(f"ERROR: {error_msg}", file=sys.stderr)
        report = {
            "status": "failed",
            "reason": f"Schema load error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }
        save_validation_report(report, OUTPUT_PATH)
        sys.exit(1)

    # Load raw logs
    try:
        with open(RAW_LOGS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        error_msg = f"Failed to load raw logs: {e}"
        print(f"ERROR: {error_msg}", file=sys.stderr)
        report = {
            "status": "failed",
            "reason": f"Data load error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }
        save_validation_report(report, OUTPUT_PATH)
        sys.exit(1)

    # Run validation using the existing API
    # The existing function returns (is_valid, report_dict)
    is_valid, report_dict = run_schema_validation(data, schema)

    # Enhance report with execution metadata
    report_dict["timestamp"] = datetime.utcnow().isoformat()
    report_dict["input_path"] = RAW_LOGS_PATH
    report_dict["schema_path"] = SCHEMA_PATH

    if is_valid:
        report_dict["status"] = "passed"
        print(f"Validation PASSED. Report written to {OUTPUT_PATH}")
        save_validation_report(report_dict, OUTPUT_PATH)
        sys.exit(0)
    else:
        report_dict["status"] = "failed"
        print(f"Validation FAILED. Report written to {OUTPUT_PATH}", file=sys.stderr)
        save_validation_report(report_dict, OUTPUT_PATH)
        sys.exit(1)

if __name__ == "__main__":
    main()
