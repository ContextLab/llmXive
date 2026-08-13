"""
Schema Validation Module.
Validates YAML schema files for structural correctness and JSON-schema compliance.
"""
import sys
import json
import yaml
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

def load_yaml_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema file and return its content as a dictionary."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_schema_structure(schema_content: Dict[str, Any]) -> bool:
    """
    Basic structural validation of the schema dictionary.
    Checks for mandatory JSON-Schema keys like $schema, type, properties.
    """
    if not isinstance(schema_content, dict):
        raise ValueError("Schema content must be a dictionary.")
    
    if "$schema" not in schema_content:
        raise ValueError("Schema missing '$schema' declaration.")
    
    if "type" not in schema_content:
        raise ValueError("Schema missing 'type' declaration.")
    
    if "properties" not in schema_content:
        raise ValueError("Schema missing 'properties' definition.")
    
    return True

def validate_with_jsonschema(schema_path: str, sample_path: Optional[str] = None) -> bool:
    """
    Validates the schema syntax using the jsonschema library.
    If a sample_path is provided, validates the sample against the schema.
    """
    try:
        import jsonschema
    except ImportError:
        print("Error: 'jsonschema' package is required for validation. Install with: pip install jsonschema")
        sys.exit(1)

    schema_dict = load_yaml_schema(schema_path)
    
    # Validate that the schema itself is valid JSON-Schema
    # We create a dummy instance to check if the schema compiles
    try:
        jsonschema.Draft7Validator.check_schema(schema_dict)
        print(f"[OK] Schema '{schema_path}' is valid JSON-Schema (Draft 7).")
    except jsonschema.exceptions.SchemaError as e:
        print(f"[FAIL] Schema '{schema_path}' is invalid: {e.message}")
        return False

    if sample_path:
        sample_dict = {}
        if Path(sample_path).suffix in ['.yaml', '.yml']:
            with open(sample_path, 'r') as f:
                sample_dict = yaml.safe_load(f)
        else:
            with open(sample_path, 'r') as f:
                sample_dict = json.load(f)
        
        try:
            jsonschema.validate(instance=sample_dict, schema=schema_dict)
            print(f"[OK] Sample '{sample_path}' validates against schema.")
        except jsonschema.exceptions.ValidationError as e:
            print(f"[FAIL] Sample '{sample_path}' does not validate: {e.message}")
            return False

    return True

def run_yamllint(schema_path: str) -> bool:
    """
    Runs yamllint on the schema file to check for YAML syntax and style issues.
    """
    try:
        result = subprocess.run(
            ['yamllint', '-d', 'relaxed', schema_path],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"[OK] YAML syntax check passed for '{schema_path}'.")
            return True
        else:
            print(f"[WARN] yamllint found issues in '{schema_path}':\n{result.stdout}")
            # We treat yamllint warnings as non-fatal for schema validity, 
            # but we report them. If strict syntax errors exist, jsonschema check above usually catches them.
            return True 
    except FileNotFoundError:
        print("[WARN] 'yamllint' not installed. Skipping YAML style check.")
        return True

def main():
    """
    Main entry point for schema validation.
    Validates contracts/output.schema.yaml as per task T007b.
    """
    schema_file = "contracts/output.schema.yaml"
    
    print(f"Validating schema: {schema_file}")
    
    # 1. Load and check basic structure
    try:
        content = load_yaml_schema(schema_file)
        validate_schema_structure(content)
        print("[OK] Basic structure validation passed.")
    except (FileNotFoundError, ValueError) as e:
        print(f"[FAIL] Structure validation failed: {e}")
        sys.exit(1)

    # 2. Run yamllint
    run_yamllint(schema_file)

    # 3. Validate JSON-Schema compliance
    if not validate_with_jsonschema(schema_file):
        sys.exit(1)

    print(f"SUCCESS: {schema_file} is valid.")

if __name__ == "__main__":
    main()
