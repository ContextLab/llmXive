"""
Schema validation utilities for the research pipeline.
Supports validation of JSON and CSV data against YAML schemas.
"""
import csv
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import yaml

from config import get_contracts_dir

def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a schema from the contracts directory.

    Args:
        schema_name: Name of the schema file (e.g., 'stimulus.schema.yaml')

    Returns:
        The loaded schema as a dictionary.
    
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is not valid YAML.
    """
    contracts_dir = get_contracts_dir()
    schema_path = contracts_dir / schema_name
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_json_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a JSON object against a schema.
    
    Note: This is a simplified validation that checks required fields and basic types.
    For full JSON Schema validation, consider using the 'jsonschema' library.
    
    Args:
        data: The JSON object to validate.
        schema: The schema dictionary.
    
    Returns:
        A list of error messages. Empty if valid.
    """
    errors = []
    
    # Check required fields
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Check property types (basic implementation)
    properties = schema.get('properties', {})
    for field, value in data.items():
        if field in properties:
            prop_schema = properties[field]
            expected_type = prop_schema.get('type')
            
            if expected_type == 'string' and not isinstance(value, str):
                errors.append(f"Field '{field}' must be a string")
            elif expected_type == 'integer' and not isinstance(value, int):
                errors.append(f"Field '{field}' must be an integer")
            elif expected_type == 'number' and not isinstance(value, (int, float)):
                errors.append(f"Field '{field}' must be a number")
            elif expected_type == 'boolean' and not isinstance(value, bool):
                errors.append(f"Field '{field}' must be a boolean")
            elif expected_type == 'array' and not isinstance(value, list):
                errors.append(f"Field '{field}' must be an array")
            elif expected_type == 'object' and not isinstance(value, dict):
                errors.append(f"Field '{field}' must be an object")
            
            # Check enum constraints
            if 'enum' in prop_schema and value not in prop_schema['enum']:
                errors.append(f"Field '{field}' must be one of {prop_schema['enum']}, got {value}")
            
            # Check pattern constraints
            if 'pattern' in prop_schema and isinstance(value, str):
                import re
                if not re.match(prop_schema['pattern'], value):
                    errors.append(f"Field '{field}' does not match pattern {prop_schema['pattern']}")
            
            # Check numeric constraints
            if expected_type in ['integer', 'number']:
                if 'minimum' in prop_schema and value < prop_schema['minimum']:
                    errors.append(f"Field '{field}' must be >= {prop_schema['minimum']}")
                if 'maximum' in prop_schema and value > prop_schema['maximum']:
                    errors.append(f"Field '{field}' must be <= {prop_schema['maximum']}")
    
    return errors

def validate_csv_against_schema(csv_path: Path, schema: Dict[str, Any]) -> List[str]:
    """
    Validate a CSV file against a schema.
    
    Args:
        csv_path: Path to the CSV file.
        schema: The schema dictionary.
    
    Returns:
        A list of error messages. Empty if valid.
    """
    errors = []
    
    if not csv_path.exists():
        return [f"CSV file not found: {csv_path}"]
    
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        if headers is None:
            return ["CSV file is empty or has no headers"]
        
        # Check required headers
        for field in required_fields:
            if field not in headers:
                errors.append(f"Missing required column: {field}")
        
        # Validate rows
        row_num = 1
        for row in reader:
            row_num += 1
            for field, value in row.items():
                if field in properties and value:
                    prop_schema = properties[field]
                    expected_type = prop_schema.get('type')
                    
                    # Skip empty values for optional fields
                    if value == '':
                        continue
                    
                    if expected_type == 'integer':
                        try:
                            int(value)
                        except ValueError:
                            errors.append(f"Row {row_num}, Column '{field}': must be an integer, got '{value}'")
                    elif expected_type == 'number':
                        try:
                            float(value)
                        except ValueError:
                            errors.append(f"Row {row_num}, Column '{field}': must be a number, got '{value}'")
                    
                    # Check enum constraints
                    if 'enum' in prop_schema and value not in prop_schema['enum']:
                        errors.append(f"Row {row_num}, Column '{field}': must be one of {prop_schema['enum']}, got '{value}'")
                    
                    # Check pattern constraints
                    if 'pattern' in prop_schema:
                        import re
                        if not re.match(prop_schema['pattern'], value):
                            errors.append(f"Row {row_num}, Column '{field}': does not match pattern {prop_schema['pattern']}")
    
    return errors

def main():
    """CLI entry point for schema validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate data files against schemas.')
    parser.add_argument('--schema', type=str, required=True, help='Schema file name')
    parser.add_argument('--data', type=str, required=True, help='Data file path (JSON or CSV)')
    parser.add_argument('--format', type=str, choices=['json', 'csv'], required=True, help='Data format')
    
    args = parser.parse_args()
    
    try:
        schema = load_schema(args.schema)
        
        if args.format == 'json':
            with open(args.data, 'r', encoding='utf-8') as f:
                data = json.load(f)
            errors = validate_json_against_schema(data, schema)
        else:
            errors = validate_csv_against_schema(Path(args.data), schema)
        
        if errors:
            print("Validation failed with errors:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        else:
            print("Validation successful: No errors found.")
            sys.exit(0)
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
