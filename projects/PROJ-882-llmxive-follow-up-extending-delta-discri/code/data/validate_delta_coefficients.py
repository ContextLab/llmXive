"""
Validate the generated DelTA coefficients JSON file against the
contracts/delta_oracle.schema.yaml schema using jsonschema.

This script is intended to be run as a standalone tool:

    python code/data/validate_delta_coefficients.py

It will load the schema (YAML), load the JSON data, perform validation,
and exit with status 0 on success or a non‑zero status on failure,
printing a helpful error message.
"""

import json
import sys
from pathlib import Path

import yaml
from jsonschema import validate, ValidationError

# Default paths – these match the locations used by the rest of the project
DEFAULT_JSON_PATH = Path("data/processed/delta_coefficients.json")
DEFAULT_SCHEMA_PATH = Path("contracts/delta_oracle.schema.yaml")


def load_json(json_path: Path) -> dict:
    """Load a JSON file and return its contents."""
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_schema(schema_path: Path) -> dict:
    """Load a YAML schema file and return its contents."""
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_delta_coefficients(
    json_path: Path = DEFAULT_JSON_PATH,
    schema_path: Path = DEFAULT_SCHEMA_PATH,
) -> bool:
    """
    Validate ``json_path`` against ``schema_path`` using jsonschema.

    Returns ``True`` if validation succeeds; raises ``ValidationError`` if not.
    """
    if not json_path.is_file():
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    data = load_json(json_path)
    schema = load_schema(schema_path)

    # jsonschema.validate will raise ValidationError on failure
    validate(instance=data, schema=schema)
    return True


def main(argv=None) -> int:
    """
    Entry point for the script.

    Optional command‑line arguments:
        argv[0] – path to the JSON file (default: data/processed/delta_coefficients.json)
        argv[1] – path to the schema file (default: contracts/delta_oracle.schema.yaml)

    Returns exit code 0 on success, 1 on validation failure, 2 on other errors.
    """
    argv = argv or sys.argv[1:]

    json_path = Path(argv[0]) if len(argv) > 0 else DEFAULT_JSON_PATH
    schema_path = Path(argv[1]) if len(argv) > 1 else DEFAULT_SCHEMA_PATH

    try:
        validate_delta_coefficients(json_path, schema_path)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except ValidationError as e:
        print("JSON validation error:", file=sys.stderr)
        print(e.message, file=sys.stderr)
        # Provide a short snippet of the failing part for debugging
        if e.path:
            print(f"Failed at: {'/'.join(map(str, e.path))}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2

    print("Validation succeeded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())