"""
Script to validate schema YAML files using pyyaml.
Ensures contracts/*.schema.yaml are syntactically valid YAML.
"""
import os
import sys
import yaml
from pathlib import Path

def validate_yaml_file(file_path: Path) -> bool:
    """Attempt to load and validate a YAML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
        print(f"✓ Valid YAML: {file_path}")
        return True
    except yaml.YAMLError as e:
        print(f"✗ Invalid YAML in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"✗ Error reading {file_path}: {e}")
        return False

def main():
    contracts_dir = Path("contracts")
    if not contracts_dir.exists():
        print(f"Error: Directory {contracts_dir} does not exist.")
        sys.exit(1)

    schema_files = list(contracts_dir.glob("*.schema.yaml"))
    if not schema_files:
        print(f"Error: No .schema.yaml files found in {contracts_dir}.")
        sys.exit(1)

    all_valid = True
    for schema_file in schema_files:
        if not validate_yaml_file(schema_file):
            all_valid = False

    if all_valid:
        print("\nAll schema contracts are valid.")
        sys.exit(0)
    else:
        print("\nSome schema contracts failed validation.")
        sys.exit(1)

if __name__ == "__main__":
    main()