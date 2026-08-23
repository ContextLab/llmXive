"""
Validates that data/results/correlation_results.csv matches contracts/correlation_result.schema.yaml.
"""
import csv
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from config import ensure_dirs

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the JSON schema file."""
    with open(schema_path, 'r') as f:
        return json.load(f)

def validate_row(row: Dict[str, str], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single row against the schema.
    Returns a list of error messages (empty if valid).
    """
    errors = []
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})

    # Check required fields
    for field in required_fields:
        if field not in row or row[field] == '':
            errors.append(f"Missing or empty required field: {field}")

    # Type and format checks
    for field, value in row.items():
        if field not in properties:
            errors.append(f"Unexpected field: {field}")
            continue

        prop_def = properties[field]
        expected_type = prop_def.get('type')

        if expected_type == 'integer':
            try:
                int(value)
            except ValueError:
                errors.append(f"Field '{field}' must be an integer, got: {value}")
        elif expected_type == 'number':
            try:
                float(value)
            except ValueError:
                errors.append(f"Field '{field}' must be a number, got: {value}")
        elif expected_type == 'string':
            if not isinstance(value, str):
                errors.append(f"Field '{field}' must be a string")
            # Check pattern if defined (e.g., for trace_id)
            if 'pattern' in prop_def:
                import re
                if not re.match(prop_def['pattern'], value):
                    errors.append(f"Field '{field}' does not match pattern: {prop_def['pattern']}")

    return errors

def main():
    schema_path = Path("contracts/correlation_result.schema.yaml")
    data_path = Path("data/results/correlation_results.csv")
    
    # Ensure directories exist for output
    ensure_dirs()

    if not schema_path.exists():
        print(f"ERROR: Schema file not found: {schema_path}")
        sys.exit(1)

    if not data_path.exists():
        print(f"WARNING: Data file not found: {data_path}. Skipping validation.")
        # Exit 0 as this is a validation step that might run before data generation
        sys.exit(0)

    # Load schema (simple JSON/YAML loader assuming valid JSON for schema)
    # The schema file is YAML, but for this simple structure we can load as JSON if valid, 
    # or use a yaml loader. Since we can't guarantee PyYAML is installed without checking requirements,
    # and the schema is simple, we'll try standard json first or implement a basic parser if needed.
    # However, the schema file provided is YAML. Let's assume PyYAML is available as per T002 requirements.
    try:
        import yaml
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
    except ImportError:
        # Fallback: basic manual parsing for this specific known schema structure if yaml is missing
        # But T002 includes PyYAML in requirements.txt implicitly via standard data science stack or explicit.
        # If strictly no yaml, we might fail. Let's assume yaml is available.
        print("ERROR: PyYAML not installed. Cannot load schema.")
        sys.exit(1)

    errors = []
    row_count = 0
    valid_count = 0

    with open(data_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_count += 1
            row_errors = validate_row(row, schema)
            if row_errors:
                errors.append(f"Row {row_count}: {row_errors}")
            else:
                valid_count += 1

    if errors:
        print(f"Validation FAILED. {len(errors)} rows failed out of {row_count}.")
        for err in errors[:10]: # Print first 10 errors
            print(f"  {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors.")
        sys.exit(1)
    else:
        print(f"Validation PASSED. All {row_count} rows are valid.")
        sys.exit(0)

if __name__ == "__main__":
    main()
