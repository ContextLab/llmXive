"""
Schema Validation Utilities.
Provides functions to load YAML schemas and validate data against them.
"""
import json
import sys
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_json_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a JSON object against a YAML schema definition.
    Returns a list of error messages.
    """
    errors = []
    
    # Check required fields
    required = schema.get('required', [])
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Check property types
    properties = schema.get('properties', {})
    for field, value in data.items():
        if field in properties:
            prop_def = properties[field]
            expected_type = prop_def.get('type')
            
            if expected_type == 'string':
                if not isinstance(value, str):
                    errors.append(f"Field '{field}' must be string, got {type(value).__name__}")
            elif expected_type == 'integer':
                if not isinstance(value, int):
                    errors.append(f"Field '{field}' must be integer, got {type(value).__name__}")
            elif expected_type == 'number':
                if not isinstance(value, (int, float)):
                    errors.append(f"Field '{field}' must be number, got {type(value).__name__}")
            elif expected_type == 'boolean':
                if not isinstance(value, bool):
                    errors.append(f"Field '{field}' must be boolean, got {type(value).__name__}")
            elif expected_type == 'array':
                if not isinstance(value, list):
                    errors.append(f"Field '{field}' must be array, got {type(value).__name__}")
            elif expected_type == 'object':
                if not isinstance(value, dict):
                    errors.append(f"Field '{field}' must be object, got {type(value).__name__}")
            
            # Check enum constraints
            if 'enum' in prop_def:
                if value not in prop_def['enum']:
                    errors.append(f"Field '{field}' value '{value}' not in allowed enum: {prop_def['enum']}")
            
            # Check numeric constraints
            if expected_type in ('integer', 'number'):
                if 'minimum' in prop_def and value < prop_def['minimum']:
                    errors.append(f"Field '{field}' value {value} below minimum {prop_def['minimum']}")
                if 'maximum' in prop_def and value > prop_def['maximum']:
                    errors.append(f"Field '{field}' value {value} above maximum {prop_def['maximum']}")
    
    return errors

def validate_csv_against_schema(csv_path: Path, schema: Dict[str, Any]) -> List[str]:
    """
    Validate a CSV file against a YAML schema definition.
    Returns a list of error messages.
    """
    errors = []
    required = schema.get('required', [])
    properties = schema.get('properties', {})
    
    if not csv_path.exists():
        return [f"CSV file not found: {csv_path}"]
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        
        # Check required headers
        for field in required:
            if field not in headers:
                errors.append(f"Missing required column in CSV: {field}")
        
        # Validate rows
        row_count = 0
        for row in reader:
            row_count += 1
            for field, value in row.items():
                if field in properties:
                    prop_def = properties[field]
                    expected_type = prop_def.get('type')
                    
                    # Skip empty values for optional fields
                    if value == '':
                        continue
                    
                    # Type validation (basic string parsing for CSV)
                    if expected_type == 'integer':
                        try:
                            int(value)
                        except ValueError:
                            errors.append(f"Row {row_count}: Field '{field}' must be integer, got '{value}'")
                    elif expected_type == 'number':
                        try:
                            float(value)
                        except ValueError:
                            errors.append(f"Row {row_count}: Field '{field}' must be number, got '{value}'")
                    
                    # Enum validation
                    if 'enum' in prop_def:
                        if value not in prop_def['enum']:
                            errors.append(f"Row {row_count}: Field '{field}' value '{value}' not in allowed enum: {prop_def['enum']}")
    
    if row_count == 0:
        errors.append("CSV file is empty or has no data rows")
    
    return errors

def main():
    """CLI entry point for schema validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate data against YAML schemas")
    parser.add_argument('--schema', type=str, required=True, help="Path to YAML schema file")
    parser.add_argument('--data', type=str, required=True, help="Path to data file (JSON or CSV)")
    parser.add_argument('--format', type=str, choices=['json', 'csv'], required=True, help="Data format")
    
    args = parser.parse_args()
    
    schema_path = Path(args.schema)
    data_path = Path(args.data)
    
    try:
        schema = load_schema(schema_path)
        
        if args.format == 'json':
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            errors = validate_json_against_schema(data, schema)
        else:
            errors = validate_csv_against_schema(data_path, schema)
        
        if errors:
            print("Validation FAILED:")
            for err in errors:
                print(f"  - {err}")
            sys.exit(1)
        else:
            print("Validation PASSED")
            sys.exit(0)
            
    except Exception as e:
        print(f"Error during validation: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
