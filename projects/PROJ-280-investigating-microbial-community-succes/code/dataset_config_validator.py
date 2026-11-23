"""
Dataset Configuration Validator

Validates dataset configuration files against the schema defined in
contracts/dataset-config.schema.yaml. Provides utilities to load the schema,
validate configs, and generate sample configurations.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
import jsonschema
from jsonschema import ValidationError, SchemaError


def load_schema(schema_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the JSON schema from the specified path or default location.

    Args:
        schema_path: Path to the schema file. If None, uses default path.

    Returns:
        Dict containing the schema definition.

    Raises:
        FileNotFoundError: If schema file is not found.
        yaml.YAMLError: If schema file is invalid YAML/JSON.
    """
    if schema_path is None:
        # Default path relative to project root
        schema_path = "contracts/dataset-config.schema.yaml"

    schema_file = Path(schema_path)
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    with open(schema_file, 'r', encoding='utf-8') as f:
        # Schema might be YAML or JSON
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError:
            # Fallback to JSON
            f.seek(0)
            return json.load(f)


def validate_config(config_path: str, schema_path: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate a dataset configuration file against the schema.

    Args:
        config_path: Path to the dataset configuration JSON file.
        schema_path: Optional path to schema. If None, uses default.

    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
    """
    config_file = Path(config_path)
    if not config_file.exists():
        return False, f"Configuration file not found: {config_file}"

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in configuration file: {e}"

    try:
        schema = load_schema(schema_path)
    except FileNotFoundError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error loading schema: {e}"

    try:
        jsonschema.validate(instance=config, schema=schema)
        return True, None
    except ValidationError as e:
        return False, f"Validation error: {e.message} at path '{e.json_path}'"
    except SchemaError as e:
        return False, f"Schema error: {e.message}"


def create_sample_config(output_path: str) -> None:
    """
    Create a sample dataset configuration file at the specified path.

    This generates a template config that conforms to the schema,
    useful for users to understand the expected structure.

    Args:
        output_path: Path where the sample config will be written.
    """
    sample_config = {
        "version": "1.0.0",
        "description": "Sample dataset configuration for microbial community succession study",
        "datasets": [
            {
                "id": "PRJNA555687",
                "source": "ncbi_sra",
                "description": "Example constructed wetland microbiome dataset",
                "metadata": {
                    "wetland_type": "constructed",
                    "nutrient_removal": True,
                    "target_nutrients": ["nitrogen", "phosphorus"],
                    "sampling_stages": ["early", "mid", "mature"],
                    "location": "North America",
                    "study_period": "24_months"
                }
            }
        ]
    }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, indent=2)


def main() -> int:
    """
    Main entry point for command-line usage.

    Usage:
        python code/dataset_config_validator.py validate <config_path>
        python code/dataset_config_validator.py sample <output_path>

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    import sys

    if len(sys.argv) < 3:
        print("Usage:")
        print("  python code/dataset_config_validator.py validate <config_path>")
        print("  python code/dataset_config_validator.py sample <output_path>")
        return 1

    command = sys.argv[1]
    path_arg = sys.argv[2]

    if command == "validate":
        is_valid, error = validate_config(path_arg)
        if is_valid:
            print(f"✓ Configuration valid: {path_arg}")
            return 0
        else:
            print(f"✗ Configuration invalid: {error}")
            return 1

    elif command == "sample":
        create_sample_config(path_arg)
        print(f"✓ Sample configuration created: {path_arg}")
        return 0

    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
