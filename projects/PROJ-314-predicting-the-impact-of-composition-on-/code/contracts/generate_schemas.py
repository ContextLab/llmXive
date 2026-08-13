"""
Schema generation and validation utilities.

This module provides functions to load, validate, and export schemas
for the ceramic reliability prediction project.
"""
import yaml
import sys
from pathlib import Path
import json
import jsonschema
from typing import Dict, Any, List

from .schemas import CeramicEntry, ModelResult, export_schemas_to_yaml, load_schema, validate_schemas, validate_data_against_schema


def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a schema from a YAML file.
    
    Args:
        schema_path: Path to the schema YAML file
        
    Returns:
        Dictionary containing the schema
    """
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_schemas(schema_dir: str = "code/contracts") -> bool:
    """
    Validate that the schema files exist and are valid YAML.
    
    Args:
        schema_dir: Directory containing the schema files
        
    Returns:
        True if all schemas are valid, False otherwise
    """
    schema_files = [
        f"{schema_dir}/ceramic_entry.schema.yaml",
        f"{schema_dir}/model_result.schema.yaml"
    ]
    
    all_valid = True
    for schema_file in schema_files:
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            print(f"✓ {schema_file} is valid")
        except FileNotFoundError:
            print(f"✗ {schema_file} not found")
            all_valid = False
        except yaml.YAMLError as e:
            print(f"✗ {schema_file} is invalid YAML: {e}")
            all_valid = False
    
    return all_valid


def validate_data_against_schema(data: Dict[str, Any], schema_name: str, schema_path: str) -> bool:
    """
    Validate data against a specific schema using jsonschema.
    
    Args:
        data: Data dictionary to validate
        schema_name: Name of the schema ('CeramicEntry' or 'ModelResult')
        schema_path: Path to the schema YAML file
        
    Returns:
        True if data is valid, False otherwise
    """
    try:
        schema = load_schema(schema_path)
        jsonschema.validate(instance=data, schema=schema)
        return True
    except jsonschema.ValidationError as e:
        print(f"Validation error: {e.message}")
        return False
    except Exception as e:
        print(f"Validation failed: {e}")
        return False


def generate_schemas(output_dir: str = "code/contracts") -> None:
    """
    Generate YAML schema files from Pydantic models.
    
    Args:
        output_dir: Directory to save the YAML schema files
    """
    export_schemas_to_yaml(output_dir)


if __name__ == "__main__":
    # Generate schemas
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "code/contracts"
    generate_schemas(output_dir)
    
    # Validate schemas
    print("\nSchema validation:")
    if validate_schemas(output_dir):
        print("All schemas are valid.")
    else:
        print("Schema validation failed.")
        sys.exit(1)