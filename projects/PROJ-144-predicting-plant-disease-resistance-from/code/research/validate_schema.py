"""
Schema validation module for output contracts.
Validates contracts/output.schema.yaml using jsonschema and yamllint.
"""
import sys
import json
import yaml
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import constants for paths
try:
    from utils.constants import CONTRACTS_DIR
except ImportError:
    # Fallback if constants not fully initialized, though T004 should exist
    CONTRACTS_DIR = Path("contracts")

OUTPUT_SCHEMA_PATH = CONTRACTS_DIR / "output.schema.yaml"


def load_yaml_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load a YAML schema file and return it as a dictionary.
    
    Args:
        schema_path: Path to the YAML schema file.
        
    Returns:
        Dictionary representation of the schema.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the YAML is invalid.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        try:
            schema = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in schema file {schema_path}: {e}")
    
    return schema


def validate_schema_structure(schema: Dict[str, Any]) -> bool:
    """
    Perform basic structural validation of the schema dictionary.
    
    Args:
        schema: The loaded schema dictionary.
        
    Returns:
        True if the schema has basic required keys, False otherwise.
    """
    required_keys = ['$schema', 'type']
    for key in required_keys:
        if key not in schema:
            print(f"Validation failed: Missing required key '{key}' in schema.")
            return False
    
    if schema['type'] != 'object':
        print(f"Validation failed: Schema root type must be 'object', got '{schema['type']}'.")
        return False
    
    return True


def validate_with_jsonschema(schema_path: Path, sample_data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate the schema itself and optionally validate sample data against it.
    Uses the 'jsonschema' library.
    
    Args:
        schema_path: Path to the schema file.
        sample_data: Optional dictionary to validate against the schema.
        
    Returns:
        True if validation passes, False otherwise.
    """
    try:
        import jsonschema
    except ImportError:
        print("Error: 'jsonschema' library is not installed. Please install it via requirements.txt.")
        return False

    try:
        schema = load_yaml_schema(schema_path)
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"Error loading schema: {e}")
        return False

    # Validate the schema structure
    if not validate_schema_structure(schema):
        return False

    # Try to validate the schema against jsonschema.Draft7Validator to ensure it's valid JSON Schema
    try:
        jsonschema.Draft7Validator.check_schema(schema)
        print(f"Schema validation passed: {schema_path} is a valid JSON Schema (Draft 7).")
    except jsonschema.exceptions.SchemaError as e:
        print(f"Schema validation failed: Invalid JSON Schema structure. {e}")
        return False

    # If sample data is provided, validate it
    if sample_data:
        try:
            jsonschema.validate(instance=sample_data, schema=schema)
            print("Sample data validation passed.")
            return True
        except jsonschema.exceptions.ValidationError as e:
            print(f"Sample data validation failed: {e.message}")
            return False
    
    return True


def run_yamllint(schema_path: Path) -> bool:
    """
    Run yamllint on the schema file to check for YAML syntax and style issues.
    
    Args:
        schema_path: Path to the YAML file.
        
    Returns:
        True if yamllint passes, False otherwise.
    """
    try:
        result = subprocess.run(
            ['yamllint', '-d', 'relaxed', str(schema_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"Yamllint passed for: {schema_path}")
            return True
        else:
            print(f"Yamllint failed for: {schema_path}")
            print(result.stdout)
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("Warning: 'yamllint' command not found. Skipping YAML style check.")
        return True  # Treat as pass if tool is missing, but schema still checked by jsonschema
    except subprocess.TimeoutExpired:
        print("Error: yamllint timed out.")
        return False


def main():
    """
    Main entry point to validate the output schema.
    """
    print(f"Validating schema: {OUTPUT_SCHEMA_PATH}")
    
    if not OUTPUT_SCHEMA_PATH.exists():
        print(f"Error: Schema file not found at {OUTPUT_SCHEMA_PATH}")
        sys.exit(1)
    
    success = True
    
    # 1. Run yamllint
    if not run_yamllint(OUTPUT_SCHEMA_PATH):
        success = False
    
    # 2. Validate with jsonschema
    if not validate_with_jsonschema(OUTPUT_SCHEMA_PATH):
        success = False
    
    if success:
        print("\n=== Schema Validation Successful ===")
        sys.exit(0)
    else:
        print("\n=== Schema Validation Failed ===")
        sys.exit(1)


if __name__ == "__main__":
    main()
