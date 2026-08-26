"""
Utility module for validating data against JSON/YAML schemas.
Provides functions to validate CSV files against the defined schemas.
"""
import os
import sys
import yaml
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a YAML schema from the given path.
    
    Args:
        schema_path: Path to the schema file
        
    Returns:
        Dictionary containing the schema
        
    Raises:
        FileNotFoundError: If the schema file doesn't exist
        yaml.YAMLError: If the schema file is not valid YAML
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, "r") as f:
        return yaml.safe_load(f)

def validate_csv_against_schema(csv_path: str, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a CSV file against a JSON/YAML schema.
    
    Args:
        csv_path: Path to the CSV file
        schema: The schema dictionary
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])
    
    if not Path(csv_path).exists():
        return False, [f"CSV file not found: {csv_path}"]
    
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        if headers is None:
            return False, ["CSV file is empty or has no headers"]
        
        # Check for required fields
        missing_required = set(required_fields) - set(headers)
        if missing_required:
            errors.append(f"Missing required columns: {missing_required}")
        
        # Check for unexpected columns
        extra_columns = set(headers) - set(properties.keys())
        if extra_columns and not schema.get("additionalProperties", True):
            errors.append(f"Unexpected columns found: {extra_columns}")
        
        # Validate each row
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (1-indexed, +1 for header)
            for field in required_fields:
                if field not in row or row[field] is None or row[field] == "":
                    errors.append(f"Row {row_num}: Missing required field '{field}'")
            
            # Type validation
            for field, value in row.items():
                if field not in properties:
                    continue
                
                expected_type = properties[field].get("type")
                if value is None or value == "":
                    continue  # Already checked for required
                
                if expected_type == "integer":
                    try:
                        int(value)
                    except ValueError:
                        errors.append(f"Row {row_num}, column '{field}': Expected integer, got '{value}'")
                
                elif expected_type == "number":
                    try:
                        float(value)
                    except ValueError:
                        errors.append(f"Row {row_num}, column '{field}': Expected number, got '{value}'")
                
                elif expected_type == "string":
                    if not isinstance(value, str):
                        errors.append(f"Row {row_num}, column '{field}': Expected string, got {type(value)}")
    
    return len(errors) == 0, errors

def validate_energy_decay_csv(csv_path: str = "data/processed/energy_decay.csv") -> Tuple[bool, List[str]]:
    """
    Validate the energy_decay.csv file against the energy schema.
    
    Args:
        csv_path: Path to the energy_decay.csv file
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    schema_path = "contracts/energy_schema.schema.yaml"
    try:
        schema = load_schema(schema_path)
        return validate_csv_against_schema(csv_path, schema)
    except FileNotFoundError as e:
        return False, [str(e)]

def main():
    """Main entry point for command-line validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate CSV files against JSON/YAML schemas")
    parser.add_argument("--schema", type=str, default="contracts/energy_schema.schema.yaml",
                      help="Path to the schema file")
    parser.add_argument("--csv", type=str, default="data/processed/energy_decay.csv",
                      help="Path to the CSV file to validate")
    
    args = parser.parse_args()
    
    try:
        schema = load_schema(args.schema)
        is_valid, errors = validate_csv_against_schema(args.csv, schema)
        
        if is_valid:
            print(f"✓ {args.csv} is valid according to {args.schema}")
            sys.exit(0)
        else:
            print(f"✗ {args.csv} has validation errors:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in schema file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()