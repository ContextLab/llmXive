"""
Runtime schema validation for session data.

This module provides the `validate_session` function which loads the JSON schema
from `contracts/session.schema.yaml` and validates incoming session data dictionaries
against it.

CRITICAL: If validation fails, this function raises a ValueError. It does NOT
return False to allow silent failure. This enforces the "fail loudly" policy
preventing non-conforming data from being written to `data/raw/`.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Attempt to import jsonschema. If missing, we raise a clear ImportError
# rather than silently failing, as schema validation is a hard requirement.
try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    # Fallback to a clear error message if the library is not installed.
    # This should be caught by the project's dependency check, but we guard here.
    raise ImportError(
        "The 'jsonschema' package is required for T019c (schema validation). "
        "Please ensure it is installed (e.g., via requirements.txt)."
    )

# Define the path to the schema relative to the project root.
# We assume this file is run from the project root or we adjust the path.
def _get_schema_path() -> Path:
    """Locate the session schema file."""
    # Try relative to current working directory first
    cwd_schema = Path("contracts/session.schema.yaml")
    if cwd_schema.exists():
        return cwd_schema

    # Try relative to this file's location (code/simulator/)
    # This handles cases where the script is run from a different directory
    base_dir = Path(__file__).resolve().parent.parent
    schema_path = base_dir / "contracts" / "session.schema.yaml"
    
    if schema_path.exists():
        return schema_path

    raise FileNotFoundError(
        f"Schema file not found at expected locations: {cwd_schema} or {schema_path}. "
        "Ensure T019b (schema generation) has been completed."
    )

def load_schema() -> Dict[str, Any]:
    """
    Load the JSON schema from the YAML file.
    
    Note: jsonschema expects a dict. We use a simple YAML loader.
    Since pyyaml is a standard dependency in this project (T002), we use it.
    """
    schema_path = _get_schema_path()
    try:
        import yaml
    except ImportError:
        raise ImportError("The 'pyyaml' package is required to load the schema.")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    if not isinstance(schema, dict):
        raise ValueError(f"Schema file {schema_path} did not load as a dictionary.")
            
    return schema

def validate_session(data: Dict[str, Any]) -> bool:
    """
    Validate a session data dictionary against the contract schema.

    Args:
        data (dict): The session data to validate.

    Returns:
        bool: True if validation passes.

    Raises:
        FileNotFoundError: If the schema file is missing (T019b not done).
        ValueError: If the data fails schema validation.
        ImportError: If jsonschema or pyyaml are missing.
    """
    if not isinstance(data, dict):
        raise ValueError("Session data must be a dictionary.")

    schema = load_schema()

    try:
        # Draft7Validator is standard for the draft-07 schema used in T019b
        validator = Draft7Validator(schema)
        errors = list(validator.iter_errors(data))
        
        if errors:
            error_messages = [
                f"Path: {' -> '.join(str(e) for e in error.path)}: {error.message}"
                for error in errors
            ]
            raise ValueError(
                f"Session data failed schema validation:\n" + "\n".join(error_messages)
            )
        
        return True

    except jsonschema.SchemaError as e:
        raise ValueError(f"Invalid schema definition in contract file: {e.message}")

def main():
    """
    CLI entry point for manual testing of the validator.
    Usage: python -m code.simulator.validator --input <path_to_json>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate session data against schema.")
    parser.add_argument("--input", type=str, required=True, help="Path to JSON file to validate.")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Validating {input_path}...")
        if validate_session(data):
            print("✓ Validation PASSED.")
            sys.exit(0)
        else:
            # Should not reach here due to raise in validate_session
            print("✗ Validation FAILED.")
            sys.exit(1)
    except ValueError as e:
        print(f"✗ Validation FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
