"""
Utility script to validate data artifacts against their JSON Schema contracts.
Used by T011 to verify study_records_raw.json.
"""
import json
import sys
import os
from pathlib import Path
import yaml

# Ensure jsonschema is available (added in requirements.txt by T003)
try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema library not found. Please install it (e.g., pip install jsonschema).")
    sys.exit(1)

from jsonschema import validate, ValidationError

def validate_file_against_schema(data_path, schema_path):
    """
    Validates a JSON data file against a YAML JSON schema.
    """
    data_file = Path(data_path)
    schema_file = Path(schema_path)

    if not data_file.exists():
        print(f"FAIL: Data file not found: {data_file}")
        return False

    if not schema_file.exists():
        print(f"FAIL: Schema file not found: {schema_file}")
        return False

    # Load Schema
    try:
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)
    except Exception as e:
        print(f"FAIL: Could not load schema {schema_file}: {e}")
        return False

    # Load Data
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"FAIL: Invalid JSON in {data_file}: {e}")
        return False
    except Exception as e:
        print(f"FAIL: Could not load data {data_file}: {e}")
        return False

    # Normalize to list if single object
    if not isinstance(data, list):
        data = [data]

    if len(data) == 0:
        print(f"FAIL: Data file {data_file} is empty.")
        return False

    # Validate
    errors = []
    for i, record in enumerate(data):
        try:
            validate(instance=record, schema=schema)
        except ValidationError as e:
            errors.append(f"Record {i}: {e.message} (Path: {' -> '.join(str(p) for p in e.absolute_path)})")

    if errors:
        print(f"FAIL: Schema validation failed for {len(errors)} record(s) in {data_file}:")
        for err in errors[:5]: # Show first 5
            print(f"  - {err}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more errors.")
        return False

    print(f"PASS: {len(data)} records in {data_file} validated successfully against {schema_file.name}.")
    return True

if __name__ == "__main__":
    # Default paths for T011
    data_path = "data/derived/study_records_raw.json"
    schema_path = "specs/contracts/study_record.schema.yaml"

    # Allow override via args
    if len(sys.argv) >= 3:
        data_path = sys.argv[1]
        schema_path = sys.argv[2]

    success = validate_file_against_schema(data_path, schema_path)
    sys.exit(0 if success else 1)
