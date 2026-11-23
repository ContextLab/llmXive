"""
Schema validation module for llmXive project.
Provides functions to validate JSON/YAML data against JSON Schema definitions.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

# Try to import jsonschema, fallback to a simple manual validator if missing
# However, for scientific rigor, jsonschema is preferred.
# We will attempt import and raise a clear error if missing.
try:
    import jsonschema
    from jsonschema import validate, ValidationError, SchemaError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


class SchemaValidationError(ValueError):
    """Custom exception for schema validation failures."""
    pass


def _load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a JSON or YAML schema from the given path.

    Args:
        schema_path: Path to the schema file (.json or .yaml/.yml)

    Returns:
        The schema as a dictionary.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if path.suffix.lower() in ['.yaml', '.yml']:
        return yaml.safe_load(content)
    elif path.suffix.lower() == '.json':
        return json.loads(content)
    else:
        # Try to detect based on content if extension is missing
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError:
            return json.loads(content)


def validate_json(data: Dict[str, Any], schema_path: str) -> bool:
    """
    Validate data against a JSON Schema.

    Args:
        data: The data dictionary to validate.
        schema_path: Path to the JSON Schema file.

    Returns:
        True if valid.

    Raises:
        SchemaValidationError: If validation fails.
        ImportError: If jsonschema is not installed.
    """
    if not HAS_JSONSCHEMA:
        # Fallback to a very basic check if jsonschema is missing
        # This is not recommended for production but prevents immediate crash
        # if the environment is minimal. However, per constraints, we should
        # ideally fail loudly if the tool is missing for a rigorous task.
        # We will raise an error to force installation of jsonschema.
        raise ImportError(
            "The 'jsonschema' package is required for robust validation. "
            "Please install it: pip install jsonschema"
        )

    schema = _load_schema(schema_path)

    try:
        validate(instance=data, schema=schema)
        return True
    except ValidationError as e:
        raise SchemaValidationError(
            f"Validation failed for {schema_path}: {e.message} "
            f"(at path: {'/'.join(str(p) for p in e.path)})"
        ) from e
    except SchemaError as e:
        raise SchemaValidationError(f"Invalid schema definition: {e.message}") from e


def validate_file(file_path: str, schema_path: str) -> bool:
    """
    Load a JSON/YAML file and validate it against a schema.

    Args:
        file_path: Path to the data file to validate.
        schema_path: Path to the JSON Schema file.

    Returns:
        True if valid.

    Raises:
        SchemaValidationError: If validation fails.
        FileNotFoundError: If the data file is missing.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    if path.suffix.lower() in ['.yaml', '.yml']:
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise SchemaValidationError(f"Failed to parse YAML file {file_path}: {e}") from e
    elif path.suffix.lower() == '.json':
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise SchemaValidationError(f"Failed to parse JSON file {file_path}: {e}") from e
    else:
        # Attempt to parse as JSON first, then YAML
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            try:
                data = yaml.safe_load(content)
            except yaml.YAMLError:
                raise SchemaValidationError(f"Could not parse file {file_path} as JSON or YAML")

    return validate_json(data, schema_path)


def main():
    """CLI entry point for schema validation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate a data file against a JSON Schema."
    )
    parser.add_argument(
        "file",
        type=str,
        help="Path to the data file (JSON or YAML) to validate."
    )
    parser.add_argument(
        "--schema",
        type=str,
        required=True,
        help="Path to the JSON Schema file."
    )

    args = parser.parse_args()

    try:
        validate_file(args.file, args.schema)
        print(f"SUCCESS: {args.file} is valid according to {args.schema}")
        sys.exit(0)
    except (FileNotFoundError, SchemaValidationError, ImportError) as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
