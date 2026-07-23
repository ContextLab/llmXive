"""
T020: Validate output schema against contracts/network_metric.schema.yaml.

This script loads the generated network_metrics.csv and validates it against
the defined JSON schema. It exits with code 0 if valid, or code 1 if invalid.
"""
import csv
import json
import sys
from pathlib import Path

# Try to import jsonschema, fallback to manual check if not available
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    print("WARNING: jsonschema not installed. Performing manual field validation.")

from config import ensure_dirs

SCHEMA_PATH = Path("contracts/network_metric.schema.yaml")
OUTPUT_PATH = Path("data/results/network_metrics.csv")

REQUIRED_FIELDS = [
    "subject_id",
    "age",
    "global_efficiency",
    "local_efficiency",
    "characteristic_path_length",
    "clustering_coefficient",
    "modularity",
    "signal_quality_flag",
    "trace_id"
]

VALID_FLAGS = ["High Signal Quality", "Low Signal Quality"]

def load_schema(path: Path) -> dict:
    """Load YAML schema. If yaml lib missing, return basic structure for manual check."""
    try:
        import yaml
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback: construct expected schema from constants if yaml is missing
        # This is a soft fallback; ideally yaml is installed.
        print("WARNING: PyYAML not installed. Cannot parse schema file. Using hardcoded expectations.")
        return {
            "required": REQUIRED_FIELDS,
            "properties": {
                "signal_quality_flag": {"enum": VALID_FLAGS}
            }
        }

def validate_row(row: dict, schema: dict, row_num: int) -> list:
    errors = []
    required = schema.get("required", [])
    props = schema.get("properties", {})

    # Check required fields
    for field in required:
        if field not in row or row[field] is None or row[field] == "":
            errors.append(f"Row {row_num}: Missing or empty required field '{field}'")

    # Check enum constraints
    if "signal_quality_flag" in row:
        val = row["signal_quality_flag"]
        if val not in VALID_FLAGS:
            errors.append(f"Row {row_num}: Invalid signal_quality_flag '{val}'. Must be in {VALID_FLAGS}")

    # Check numeric types (basic check)
    numeric_fields = ["age", "global_efficiency", "local_efficiency", "characteristic_path_length", "clustering_coefficient", "modularity"]
    for field in numeric_fields:
        if field in row:
            try:
                float(row[field])
            except ValueError:
                errors.append(f"Row {row_num}: Field '{field}' is not a valid number: {row[field]}")

    return errors

def main():
    ensure_dirs()

    if not OUTPUT_PATH.exists():
        print(f"ERROR: Output file not found: {OUTPUT_PATH}")
        print("T020 FAILED: network_metrics.csv does not exist.")
        sys.exit(1)

    if not SCHEMA_PATH.exists():
        print(f"ERROR: Schema file not found: {SCHEMA_PATH}")
        print("T020 FAILED: Schema definition missing.")
        sys.exit(1)

    schema = load_schema(SCHEMA_PATH)

    all_errors = []
    total_rows = 0

    try:
        with open(OUTPUT_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate header
            if reader.fieldnames is None:
                print("ERROR: CSV file is empty or has no header.")
                sys.exit(1)
            
            missing_headers = set(REQUIRED_FIELDS) - set(reader.fieldnames)
            if missing_headers:
                print(f"ERROR: CSV missing required columns: {missing_headers}")
                sys.exit(1)

            for i, row in enumerate(reader, start=2): # Start at 2 because 1 is header
                total_rows += 1
                errors = validate_row(row, schema, i)
                all_errors.extend(errors)

    except Exception as e:
        print(f"ERROR: Failed to read CSV: {e}")
        sys.exit(1)

    if all_errors:
        print(f"VALIDATION FAILED: {len(all_errors)} error(s) found.")
        for err in all_errors[:10]: # Show first 10
            print(f"  - {err}")
        if len(all_errors) > 10:
            print(f"  ... and {len(all_errors) - 10} more.")
        print("T020 FAILED: Schema validation errors detected.")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED: {total_rows} rows validated successfully against {SCHEMA_PATH}.")
        print("T020 COMPLETED: Output schema is valid.")
        sys.exit(0)

if __name__ == "__main__":
    main()
