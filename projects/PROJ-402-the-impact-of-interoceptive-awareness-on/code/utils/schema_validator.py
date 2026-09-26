import os
import sys
import json
import csv
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

class SchemaValidationError(Exception):
    """Schema validation error."""
    pass

class FileLoadError(Exception):
    """File load error."""
    pass

def load_schema_from_file(schema_path: Optional[str] = None) -> Dict[str, Any]:
    """Load schema from file.
    
    Args:
        schema_path: Path to the schema file. Defaults to contracts/dataset.schema.yaml.
        
    Returns:
        Dictionary containing the schema.
        
    Raises:
        FileLoadError: If the schema file cannot be loaded.
    """
    if schema_path is None:
        # Default path relative to project root
        schema_path = "contracts/dataset.schema.yaml"
    
    path = Path(schema_path)
    if not path.exists():
        raise FileLoadError(f"Schema file not found: {schema_path}")
    
    try:
        with open(path, 'r') as f:
            schema = yaml.safe_load(f)
        return schema
    except yaml.YAMLError as e:
        raise FileLoadError(f"Failed to parse YAML schema: {e}")
    except Exception as e:
        raise FileLoadError(f"Failed to load schema file: {e}")

def validate_data_against_schema(data: List[Dict[str, Any]], schema: Dict[str, Any]) -> List[str]:
    """Validate data against schema.
    
    Args:
        data: List of dictionaries representing rows.
        schema: The JSON Schema dictionary.
        
    Returns:
        List of validation error messages. Empty if valid.
    """
    errors = []
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})
    
    for i, row in enumerate(data):
        # Check required fields
        for field in required_fields:
            if field not in row or row[field] is None:
                errors.append(f"Row {i}: Missing required field '{field}'")
        
        # Check field types and constraints
        for field, value in row.items():
            if field in properties:
                prop_schema = properties[field]
                
                # Check type
                expected_type = prop_schema.get('type')
                if expected_type == 'string' and not isinstance(value, str):
                    # Allow None for optional fields, but check required earlier
                    if value is not None:
                        errors.append(f"Row {i}, field '{field}': Expected string, got {type(value).__name__}")
                elif expected_type == 'number' and not isinstance(value, (int, float)):
                    if value is not None:
                        errors.append(f"Row {i}, field '{field}': Expected number, got {type(value).__name__}")
                
                # Check enum constraints
                if 'enum' in prop_schema and value is not None:
                    if value not in prop_schema['enum']:
                        errors.append(f"Row {i}, field '{field}': Value '{value}' not in allowed values {prop_schema['enum']}")
    
    return errors

def validate_file_against_schema(file_path: str, schema_path: Optional[str] = None) -> Dict[str, Any]:
    """Validate a TSV/CSV file against the schema.
    
    Args:
        file_path: Path to the data file (TSV or CSV).
        schema_path: Path to the schema file.
        
    Returns:
        Dictionary with 'valid' (bool) and 'errors' (list of strings).
        
    Raises:
        FileLoadError: If the data file cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileLoadError(f"Data file not found: {file_path}")
    
    # Load schema
    schema = load_schema_from_file(schema_path)
    
    # Read data
    data = []
    try:
        if path.suffix.lower() == '.tsv':
            with open(path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                data = list(reader)
        elif path.suffix.lower() == '.csv':
            with open(path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
        else:
            raise FileLoadError(f"Unsupported file format: {path.suffix}. Expected .tsv or .csv")
    except Exception as e:
        raise FileLoadError(f"Failed to read data file: {e}")
    
    # Validate
    errors = validate_data_against_schema(data, schema)
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'rows_validated': len(data)
    }

def validate_contract_input(input_data: Any) -> bool:
    """Validate contract input (placeholder for future use).
    
    Args:
        input_data: Input data to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    # For now, just check if it's not None
    return input_data is not None

def main():
    """Main entry point for schema validator.
    
    Usage:
        python -m code.utils.schema_validator <file_path> [schema_path]
        
    Exit codes:
        0: Validation successful
        1: Validation failed
        2: File load error (missing file, invalid format)
        3: Schema load error
    """
    if len(sys.argv) < 2:
        print("Usage: python -m code.utils.schema_validator <file_path> [schema_path]")
        print("  file_path: Path to the TSV/CSV file to validate")
        print("  schema_path: (Optional) Path to the schema file")
        sys.exit(2)
    
    file_path = sys.argv[1]
    schema_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result = validate_file_against_schema(file_path, schema_path)
        
        if result['valid']:
            print(f"Validation successful: {result['rows_validated']} rows validated.")
            sys.exit(0)
        else:
            print(f"Validation failed with {len(result['errors'])} errors:")
            for error in result['errors']:
                print(f"  - {error}")
            sys.exit(1)
            
    except FileLoadError as e:
        print(f"File load error: {e}")
        sys.exit(2)
    except SchemaValidationError as e:
        print(f"Schema validation error: {e}")
        sys.exit(3)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()