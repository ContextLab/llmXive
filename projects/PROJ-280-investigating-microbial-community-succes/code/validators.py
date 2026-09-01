"""
Dataset configuration validation utilities.
Implements T004_script: validate_dataset_config function.
"""
import json
import re
import sys
import os
from pathlib import Path
from typing import Optional

import yaml
from jsonschema import validate, ValidationError

# Regex patterns for validation
VALID_SRA = re.compile(r'^(SRR|ERR)[0-9]+$')
VALID_ZENDO = re.compile(r'^10\.5281/zenodo\.[0-9]+$')

def load_schema(schema_path: str) -> dict:
    """Load the JSON schema from a YAML file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_dataset_config(config_path: str) -> bool:
    """
    Validate the dataset configuration JSON against the schema and custom rules.

    Args:
        config_path: Path to the dataset_ids.json file.

    Returns:
        True if valid, False otherwise (and prints error to stderr).
    """
    try:
        # Resolve paths relative to project root if needed, but assume absolute or relative to CWD
        config_file = Path(config_path)
        schema_file = Path("contracts/dataset-config.schema.yaml")

        if not config_file.exists():
            print(f"Validation failed: Config file not found: {config_path}", file=sys.stderr)
            return False

        if not schema_file.exists():
            print(f"Validation failed: Schema file not found: {schema_file}", file=sys.stderr)
            return False

        # Load data
        with open(config_file, 'r') as f:
            data = json.load(f)

        # Load schema
        schema = load_schema(str(schema_file))

        # Validate structure
        validate(instance=data, schema=schema)

        # Custom validation rules
        for ds in data['datasets']:
            if ds['source'] == 'NCBI_SRA':
                if not VALID_SRA.match(ds['id']):
                    raise ValueError(f"Invalid SRA ID: {ds['id']}")
            elif ds['source'] == 'Zenodo':
                if not VALID_ZENDO.match(ds['url']):
                    raise ValueError(f"Invalid Zenodo URL: {ds['url']}")

        return True

    except ValidationError as e:
        print(f"Validation failed: JSON Schema Error - {e.message}", file=sys.stderr)
        return False
    except json.JSONDecodeError as e:
        print(f"Validation failed: Invalid JSON - {e}", file=sys.stderr)
        return False
    except ValueError as e:
        print(f"Validation failed: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Validation failed: Unexpected error - {e}", file=sys.stderr)
        return False

def main():
    """CLI entry point for validation."""
    config_path = "data/config/dataset_ids.json"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    if validate_dataset_config(config_path):
        print("Validation successful.")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()