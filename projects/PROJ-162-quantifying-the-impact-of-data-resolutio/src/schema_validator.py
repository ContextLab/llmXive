"""
Schema validation module for llmXive project.

Provides functions to validate JSON data against YAML/JSON schemas
and CLI entry point for file validation.
"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from jsonschema import validate, ValidationError, Draft7Validator

class SchemaValidationError(Exception):
    """Custom exception for schema validation failures."""
    pass

def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a schema from a YAML or JSON file.
    
    Args:
        schema_path: Path to the schema file (.yaml, .yml, or .json)
        
    Returns:
        Dictionary containing the schema definition
        
    Raises:
        FileNotFoundError: If schema file doesn't exist
        ValueError: If schema file format is unsupported
    """
    path = Path(schema_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    
    suffix = path.suffix.lower()
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            if suffix in ['.yaml', '.yml']:
                schema = yaml.safe_load(f)
            elif suffix == '.json':
                schema = json.load(f)
            else:
                raise ValueError(f"Unsupported schema format: {suffix}. Use .yaml, .yml, or .json")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in schema file {path}: {e}")
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in schema file {path}: {e}")
    
    if schema is None:
        raise ValueError(f"Schema file {path} is empty or invalid")
        
    return schema

def validate_json(data: Dict[str, Any], schema_path: Union[str, Path]) -> None:
    """
    Validate JSON data against a schema.
    
    Args:
        data: Dictionary containing the data to validate
        schema_path: Path to the schema file
        
    Raises:
        SchemaValidationError: If validation fails
        FileNotFoundError: If schema file doesn't exist
        ValueError: If schema file is invalid
    """
    schema = load_schema(schema_path)
    
    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        error_path = ".".join(str(p) for p in e.path) if e.path else "root"
        raise SchemaValidationError(
            f"Validation failed for '{error_path}': {e.message}"
        ) from e

def validate_file(file_path: Union[str, Path], schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Validate a JSON file against a schema.
    
    Args:
        file_path: Path to the JSON file to validate
        schema_path: Path to the schema file
        
    Returns:
        The validated data as a dictionary
        
    Raises:
        SchemaValidationError: If validation fails
        FileNotFoundError: If file or schema doesn't exist
        ValueError: If file is not valid JSON
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in data file {path}: {e}")
    
    validate_json(data, schema_path)
    return data

def main():
    """CLI entry point for schema validation."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate a JSON file against a YAML/JSON schema"
    )
    parser.add_argument(
        "file",
        type=str,
        help="Path to the JSON file to validate"
    )
    parser.add_argument(
        "--schema", "-s",
        type=str,
        required=True,
        help="Path to the schema file (YAML or JSON)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed validation information"
    )
    
    args = parser.parse_args()
    
    try:
        validated_data = validate_file(args.file, args.schema)
        
        if args.verbose:
            print(f"✓ Validation successful for: {args.file}")
            print(f"  Schema: {args.schema}")
            print(f"  Keys: {list(validated_data.keys())}")
        else:
            print(f"✓ Valid")
        
        sys.exit(0)
        
    except FileNotFoundError as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"✗ Invalid format: {e}", file=sys.stderr)
        sys.exit(2)
    except SchemaValidationError as e:
        print(f"✗ Validation failed: {e}", file=sys.stderr)
        sys.exit(3)

if __name__ == "__main__":
    main()
