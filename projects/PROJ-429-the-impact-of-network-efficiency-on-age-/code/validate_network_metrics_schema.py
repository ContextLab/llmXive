"""
Validates the output of network metric calculations against the defined schema.
Task: T020 - Validate output schema against contracts/network_metric.schema.yaml.
"""
import csv
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

from config import ensure_dirs


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the JSON/YAML schema from file."""
    # Simple YAML loader for this specific schema (no external deps if possible, 
    # but standard PyYAML is expected in requirements)
    try:
        import yaml
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback if yaml is not installed, though requirements.txt should have it
        # For this specific schema, we can parse it manually if needed, 
        # but let's assume PyYAML is available as per T002.
        print("Error: PyYAML is required to load the schema.", file=sys.stderr)
        sys.exit(1)


def validate_row(row: Dict[str, str], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates a single row from the CSV against the schema.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})

    # Check required fields
    for field in required_fields:
        if field not in row or row[field] is None or row[field] == '':
            errors.append(f"Missing required field: {field}")

    # Type and format validation
    for field, value in row.items():
        if field in properties:
            field_schema = properties[field]
            field_type = field_schema.get('type')
            
            # Check for empty strings in required fields (already checked above, but double check)
            if not value and field in required_fields:
                continue # Already reported

            try:
                if field_type == 'integer':
                    int(value)
                elif field_type == 'number':
                    float(value)
                elif field_type == 'string':
                    if 'pattern' in field_schema:
                        import re
                        if not re.match(field_schema['pattern'], value):
                            errors.append(f"Field '{field}' does not match pattern: {field_schema['pattern']}")
                    if 'enum' in field_schema:
                        if value not in field_schema['enum']:
                            errors.append(f"Field '{field}' value '{value}' not in allowed enum: {field_schema['enum']}")
                # Add more type checks if necessary
            except ValueError as e:
                errors.append(f"Field '{field}' has invalid type (expected {field_type}): {value}")

    return len(errors) == 0, errors


def main():
    """Main entry point for schema validation."""
    ensure_dirs()
    
    csv_path = Path("data/results/network_metrics.csv")
    schema_path = Path("contracts/network_metric.schema.yaml")
    
    if not csv_path.exists():
        print(f"Error: Input file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)
    
    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_path}", file=sys.stderr)
        sys.exit(1)

    schema = load_schema(schema_path)
    
    valid_count = 0
    invalid_count = 0
    total_count = 0
    errors_log = []

    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            total_count += 1
            is_valid, errors = validate_row(row, schema)
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                errors_log.append({
                    "row_index": i + 1, # 1-based index
                    "participant_id": row.get('participant_id', 'N/A'),
                    "errors": errors
                })

    print(f"Validation Complete: {total_count} rows processed.")
    print(f"Valid: {valid_count}, Invalid: {invalid_count}")

    if invalid_count > 0:
        print("Validation failed for some rows. Details:")
        for err in errors_log:
            print(f"  Row {err['row_index']} (ID: {err['participant_id']}): {err['errors']}")
        sys.exit(1)
    else:
        print("All rows validated successfully against the schema.")
        sys.exit(0)


if __name__ == "__main__":
    main()