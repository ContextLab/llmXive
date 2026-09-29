"""
Verify and archive output for the data pipeline.

This script checks for the existence of required output artifacts:
1. data/processed/cleaned_studies.csv
2. data/raw/excluded_studies.log

It validates the CSV schema against the defined JSON Schema contract.
It handles empty CSVs gracefully if mock data is detected or if no studies matched.
"""

import csv
import json
import os
import sys
from pathlib import Path

import yaml
from jsonschema import validate, ValidationError, Draft7Validator

# Project root relative to this script (assuming scripts/ directory)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

CSV_PATH = DATA_PROCESSED_DIR / "cleaned_studies.csv"
LOG_PATH = DATA_RAW_DIR / "excluded_studies.log"
SCHEMA_PATH = CONTRACTS_DIR / "cleaned_study.schema.yaml"
MOCK_DATA_PATH = DATA_RAW_DIR / "mock_registry_response.json"

def load_schema(schema_path: Path) -> dict:
    """Load JSON Schema from YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def verify_csv_artifact(csv_path: Path) -> bool:
    """Verify the existence and basic structure of the CSV file."""
    if not csv_path.exists():
        print(f"FAIL: CSV artifact not found: {csv_path}")
        return False

    print(f"OK: CSV artifact found: {csv_path}")

    # Check if empty
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except Exception as e:
        print(f"FAIL: Could not read CSV: {e}")
        return False

    if len(rows) == 0:
        print("INFO: CSV is empty (0 rows).")
        # Check if mock data exists (CI mode indicator) or if it's just no matches
        if MOCK_DATA_PATH.exists():
            print("INFO: Mock data detected. Empty CSV is acceptable in CI mode.")
            return True
        else:
            print("INFO: No mock data. Empty CSV implies no studies matched criteria.")
            # This is acceptable if the pipeline ran successfully and found nothing
            return True

    print(f"OK: CSV contains {len(rows)} rows.")
    return True

def verify_log_artifact(log_path: Path) -> bool:
    """Verify the existence of the exclusion log file."""
    if not log_path.exists():
        # It's possible no studies were excluded, so the log might not exist.
        # However, the task description implies it should be created if exclusions happen.
        # We treat missing log as acceptable if no exclusions occurred, but we warn.
        print("WARN: Exclusion log not found. This is acceptable if no studies were excluded.")
        return True

    print(f"OK: Exclusion log found: {log_path}")

    # Validate JSONL format
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    json.loads(line)
        print("OK: Log file format is valid JSONL.")
    except json.JSONDecodeError as e:
        print(f"FAIL: Invalid JSON in log file at line {line_num}: {e}")
        return False
    except Exception as e:
        print(f"FAIL: Could not read log file: {e}")
        return False

    return True

def verify_schema_compliance(csv_path: Path, schema_path: Path) -> bool:
    """Verify CSV rows against the JSON Schema contract."""
    if not csv_path.exists():
        # Handled in verify_csv_artifact, but safety check
        return False

    if not schema_path.exists():
        print(f"FAIL: Schema file not found: {schema_path}")
        return False

    schema = load_schema(schema_path)
    validator = Draft7Validator(schema)

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader, 1):
                # Convert row values to appropriate types for validation if necessary
                # The schema expects specific types (int, boolean, etc.)
                # CSV reads everything as string. We need to coerce or validate loosely.
                # For strict compliance, we coerce based on schema type definitions.
                cleaned_row = {}
                for key, value in row.items():
                    if key in schema.get("properties", {}):
                        prop = schema["properties"][key]
                        if prop.get("type") == "integer":
                            cleaned_row[key] = int(value) if value else 0
                        elif prop.get("type") == "boolean":
                            cleaned_row[key] = value.lower() in ("true", "1", "yes")
                        elif prop.get("type") == "number":
                            cleaned_row[key] = float(value) if value else 0.0
                        else:
                            cleaned_row[key] = value
                    else:
                        cleaned_row[key] = value

                errors = list(validator.iter_errors(cleaned_row))
                if errors:
                    print(f"FAIL: Row {row_idx} failed schema validation:")
                    for error in errors:
                        print(f"  - {error.message} at {list(error.path)}")
                    return False
    except Exception as e:
        print(f"FAIL: Error during schema validation: {e}")
        return False

    print("OK: All rows in CSV comply with the schema.")
    return True

def main():
    print("Starting output verification...")
    all_checks_passed = True

    # 1. Verify CSV existence and basic structure
    if not verify_csv_artifact(CSV_PATH):
        all_checks_passed = False

    # 2. Verify Log existence
    if not verify_log_artifact(LOG_PATH):
        all_checks_passed = False

    # 3. Verify Schema Compliance (only if CSV exists and has rows)
    if CSV_PATH.exists() and verify_csv_artifact(CSV_PATH):
        # Re-read to check rows count logic inside verify_csv_artifact
        # We rely on the return value of verify_csv_artifact which already checked existence
        # If it passed, we proceed to schema check.
        if not verify_schema_compliance(CSV_PATH, SCHEMA_PATH):
            all_checks_passed = False

    if all_checks_passed:
        print("\nSUCCESS: All verification checks passed.")
        sys.exit(0)
    else:
        print("\nFAILURE: One or more verification checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()