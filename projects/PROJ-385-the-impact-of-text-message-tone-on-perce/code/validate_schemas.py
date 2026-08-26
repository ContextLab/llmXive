"""
Schema validation utilities for CSV and JSON files.
Used by contract tests to ensure data artifacts match specifications.
"""
import csv
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import yaml


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_json_against_schema(json_path: Path, schema: Dict[str, Any]) -> List[str]:
    """
    Validates a JSON file against a JSON Schema (draft-07 compatible).
    Returns a list of error messages. Empty list means valid.
    """
    try:
        import jsonschema
    except ImportError:
        return ["Error: jsonschema library not installed. Run: pip install jsonschema"]

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(data))
    
    if errors:
        return [f"JSON Error: {e.message} at {list(e.path)}" for e in errors]
    return []


def validate_csv_against_schema(csv_path: Path, schema: Dict[str, Any]) -> List[str]:
    """
    Validates a CSV file against a schema definition.
    
    Expected Schema Format (YAML):
    ---
    type: object
    properties:
      column_name:
        type: string  # or integer, number, boolean
        required: true
        # optional: min_value, max_value, pattern (regex)
    
    Returns a list of error messages.
    """
    errors = []
    
    if not csv_path.exists():
        return [f"File not found: {csv_path}"]

    try:
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                return ["CSV file is empty or has no headers"]

            # Check required columns
            properties = schema.get("properties", {})
            for col_name, col_def in properties.items():
                if col_def.get("required", False):
                    if col_name not in headers:
                        errors.append(f"Missing required column: {col_name}")
            
            if errors:
                return errors

            # Validate row data types and constraints
            row_num = 1 # Header is row 0, data starts at 1
            for row in reader:
                row_num += 1
                for col_name, col_def in properties.items():
                    if col_name not in row:
                        continue # Already handled by required check
                    
                    value = row[col_name]
                    col_type = col_def.get("type")
                    
                    if col_type == "integer":
                        try:
                            int(value)
                        except ValueError:
                            errors.append(f"Row {row_num}, Column '{col_name}': Expected integer, got '{value}'")
                    
                    elif col_type == "number":
                        try:
                            float(value)
                        except ValueError:
                            errors.append(f"Row {row_num}, Column '{col_name}': Expected number, got '{value}'")
                    
                    elif col_type == "boolean":
                        if value.lower() not in ("true", "false", "1", "0", "yes", "no"):
                            errors.append(f"Row {row_num}, Column '{col_name}': Expected boolean, got '{value}'")
                    
                    elif col_type == "string":
                        # Check pattern if defined
                        if "pattern" in col_def:
                            import re
                            if not re.match(col_def["pattern"], value):
                                errors.append(f"Row {row_num}, Column '{col_name}': Value '{value}' does not match pattern '{col_def['pattern']}'")
                        
                        # Check min/max length if defined
                        if "min_length" in col_def and len(value) < col_def["min_length"]:
                            errors.append(f"Row {row_num}, Column '{col_name}': Length {len(value)} < min_length {col_def['min_length']}")
                        if "max_length" in col_def and len(value) > col_def["max_length"]:
                            errors.append(f"Row {row_num}, Column '{col_name}': Length {len(value)} > max_length {col_def['max_length']}")
                    
                    # Check numeric constraints
                    if col_type in ("integer", "number"):
                        try:
                            num_val = float(value)
                            if "min_value" in col_def and num_val < col_def["min_value"]:
                                errors.append(f"Row {row_num}, Column '{col_name}': Value {num_val} < min_value {col_def['min_value']}")
                            if "max_value" in col_def and num_val > col_def["max_value"]:
                                errors.append(f"Row {row_num}, Column '{col_name}': Value {num_val} > max_value {col_def['max_value']}")
                        except ValueError:
                            pass # Already caught by type check
                    
                    # Check null/empty constraints
                    if col_def.get("required", False) and (value is None or value.strip() == ""):
                        errors.append(f"Row {row_num}, Column '{col_name}': Required field is empty")

    except Exception as e:
        errors.append(f"Error reading CSV: {str(e)}")

    return errors


def main():
    """CLI entry point for manual validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate data files against YAML schemas.")
    parser.add_argument("--csv", type=str, help="Path to CSV file to validate")
    parser.add_argument("--json", type=str, help="Path to JSON file to validate")
    parser.add_argument("--schema", type=str, required=True, help="Path to schema YAML file")
    
    args = parser.parse_args()
    schema_path = Path(args.schema)
    schema = load_schema(schema_path)
    
    if args.csv:
        csv_path = Path(args.csv)
        errors = validate_csv_against_schema(csv_path, schema)
        if errors:
            print(f"Validation FAILED for {csv_path}:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        else:
            print(f"Validation PASSED for {csv_path}")
    
    if args.json:
        json_path = Path(args.json)
        errors = validate_json_against_schema(json_path, schema)
        if errors:
            print(f"Validation FAILED for {json_path}:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        else:
            print(f"Validation PASSED for {json_path}")

if __name__ == "__main__":
    main()