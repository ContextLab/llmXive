"""
Schema validation utilities for the research pipeline.

Provides functions to load YAML schemas and validate JSON/CSV data against them.
"""
import json
import sys
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import yaml

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_json_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a JSON object against a schema.
    
    Simple validation checking for required fields and types.
    """
    errors = []
    
    # Check required fields
    required = schema.get("required", [])
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Check property types if defined
    properties = schema.get("properties", {})
    for field, spec in properties.items():
        if field in data:
            expected_type = spec.get("type")
            value = data[field]
            
            if expected_type == "string" and not isinstance(value, str):
                errors.append(f"Field '{field}' should be string, got {type(value).__name__}")
            elif expected_type == "integer" and not isinstance(value, int):
                errors.append(f"Field '{field}' should be integer, got {type(value).__name__}")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"Field '{field}' should be number, got {type(value).__name__}")
            elif expected_type == "boolean" and not isinstance(value, bool):
                errors.append(f"Field '{field}' should be boolean, got {type(value).__name__}")
    
    return len(errors) == 0, errors

def validate_csv_against_schema(csv_path: Path, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a CSV file against a schema.
    
    Checks:
    1. All required columns are present
    2. Column types match the schema definitions
    """
    errors = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        if headers is None:
            return False, ["CSV file is empty or has no headers"]
        
        # Check required columns
        required_columns = schema.get("required", [])
        for col in required_columns:
            if col not in headers:
                errors.append(f"Missing required column: {col}")
        
        # Check column types
        properties = schema.get("properties", {})
        rows = list(reader)
        
        if len(rows) == 0:
            errors.append("CSV file has no data rows")
            return len(errors) == 0, errors
        
        for col_name, spec in properties.items():
            if col_name in headers:
                expected_type = spec.get("type")
                
                # Check first non-empty value
                for row in rows:
                    value = row.get(col_name, "")
                    if value:
                        if expected_type == "string":
                            # Strings are always valid in CSV
                            break
                        elif expected_type == "integer":
                            if not value.isdigit() and not (value.startswith('-') and value[1:].isdigit()):
                                errors.append(f"Column '{col_name}' contains non-integer value: {value}")
                            break
                        elif expected_type == "number":
                            try:
                                float(value)
                            except ValueError:
                                errors.append(f"Column '{col_name}' contains non-numeric value: {value}")
                            break
                        elif expected_type == "boolean":
                            if value.lower() not in ['true', 'false', '1', '0']:
                                errors.append(f"Column '{col_name}' contains non-boolean value: {value}")
                            break
    
    return len(errors) == 0, errors

def main():
    """CLI entry point for schema validation."""
    if len(sys.argv) < 3:
        print("Usage: python validate_schemas.py <schema.yaml> <data.json|data.csv>")
        sys.exit(1)
    
    schema_path = Path(sys.argv[1])
    data_path = Path(sys.argv[2])
    
    if not schema_path.exists():
        print(f"Schema file not found: {schema_path}")
        sys.exit(1)
    
    if not data_path.exists():
        print(f"Data file not found: {data_path}")
        sys.exit(1)
    
    schema = load_schema(schema_path)
    
    if data_path.suffix == '.json':
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        is_valid, errors = validate_json_against_schema(data, schema)
    elif data_path.suffix == '.csv':
        is_valid, errors = validate_csv_against_schema(data_path, schema)
    else:
        print("Unsupported file format. Use .json or .csv")
        sys.exit(1)
    
    if is_valid:
        print("Validation passed")
        sys.exit(0)
    else:
        print("Validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
