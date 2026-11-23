"""
Script to validate data artifacts against JSON Schema contracts.
Used for T011 and general data integrity checks.
"""
import json
import sys
import os
from pathlib import Path
import yaml
from jsonschema import validate, ValidationError, SchemaError

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


def load_schema(schema_path: Path) -> dict:
    """Load YAML schema from file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_data(data_path: Path) -> list:
    """Load JSON data from file."""
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_file_against_schema(data_path: Path, schema_path: Path) -> bool:
    """
    Validate a JSON data file against a YAML schema.

    Args:
        data_path: Path to the JSON data file.
        schema_path: Path to the YAML schema file.

    Returns:
        True if valid, raises ValidationError if invalid.
    """
    schema = load_schema(schema_path)
    data = load_data(data_path)

    try:
        validate(instance=data, schema=schema)
        print(f"✓ Validation passed: {data_path.name} matches {schema_path.name}")
        return True
    except ValidationError as e:
        print(f"✗ Validation failed: {data_path.name}")
        print(f"  Error: {e.message}")
        print(f"  Path: {list(e.path)}")
        raise
    except SchemaError as e:
        print(f"✗ Schema error: {schema_path.name}")
        print(f"  Error: {e.message}")
        raise


def main():
    """Entry point for contract validation."""
    # Define paths
    data_path = PROJECT_ROOT / "data" / "derived" / "study_records_raw.json"
    schema_path = PROJECT_ROOT / "specs" / "contracts" / "study_record.schema.yaml"

    print("Running contract validation (T011)...")
    print(f"  Data: {data_path}")
    print(f"  Schema: {schema_path}")

    try:
        validate_file_against_schema(data_path, schema_path)
        print("\nContract test T011 PASSED.")
        return 0
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        return 1
    except (ValidationError, SchemaError) as e:
        print(f"\n✗ Contract test T011 FAILED.")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())