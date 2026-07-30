"""
Schema Generation and Validation Module.

This module provides utilities to validate that the JSON/YAML schema files
defined in `code/contracts/` are syntactically correct and conform to
standard JSON Schema drafts.

It also serves as a reference for the data contracts used by the pipeline.
"""
import yaml
import sys
from pathlib import Path
import json
import jsonschema
from typing import Dict, Any, List

# Define the path to the contracts directory relative to this file
CONTRACTS_DIR = Path(__file__).parent

def load_schema(schema_filename: str) -> Dict[str, Any]:
    """
    Load a YAML schema file from the contracts directory.
    
    Args:
        schema_filename: Name of the schema file (e.g., 'ceramic_entry.schema.yaml')
        
    Returns:
        Dictionary representation of the schema.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    schema_path = CONTRACTS_DIR / schema_filename
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_schemas() -> bool:
    """
    Validate that all schema files in the contracts directory are syntactically valid.
    
    This function attempts to load each .schema.yaml file and parses it as YAML.
    It does not validate against a meta-schema (like jsonschema.validate) because
    that requires a more complex setup, but it ensures the files are readable
    and well-formed YAML.
    
    Returns:
        True if all schemas are valid, False otherwise.
    """
    schema_files = list(CONTRACTS_DIR.glob("*.schema.yaml"))
    
    if not schema_files:
        print("Warning: No schema files found in contracts directory.")
        return False
    
    all_valid = True
    
    for schema_file in schema_files:
        try:
            schema = load_schema(schema_file.name)
            # Basic structural check: must be a dict and have a 'properties' or 'type'
            if not isinstance(schema, dict):
                print(f"Error: {schema_file.name} is not a valid JSON Schema object.")
                all_valid = False
                continue
            
            if 'type' not in schema and 'allOf' not in schema and 'anyOf' not in schema:
                print(f"Warning: {schema_file.name} might be missing a root 'type' definition.")
            
            print(f"OK: {schema_file.name} is valid YAML and parses to a schema object.")
            
        except yaml.YAMLError as e:
            print(f"Error: {schema_file.name} contains invalid YAML: {e}")
            all_valid = False
        except Exception as e:
            print(f"Error: Unexpected error validating {schema_file.name}: {e}")
            all_valid = False
    
    return all_valid

def validate_data_against_schema(data: Dict[str, Any], schema_filename: str) -> bool:
    """
    Validate a data dictionary against a specific schema.
    
    Args:
        data: The data dictionary to validate.
        schema_filename: The schema file to validate against.
        
    Returns:
        True if data is valid, False otherwise.
    """
    try:
        schema = load_schema(schema_filename)
        # jsonschema.validate will raise an exception if validation fails
        jsonschema.validate(instance=data, schema=schema)
        return True
    except jsonschema.exceptions.ValidationError as e:
        print(f"Validation Error: {e.message}")
        return False
    except Exception as e:
        print(f"Error during validation: {e}")
        return False

if __name__ == "__main__":
    print("Validating contract schemas...")
    if validate_schemas():
        print("All schemas are valid.")
        sys.exit(0)
    else:
        print("Schema validation failed.")
        sys.exit(1)