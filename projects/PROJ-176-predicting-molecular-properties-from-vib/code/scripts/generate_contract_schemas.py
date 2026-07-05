"""
Script to generate and validate contract schema files.
This script ensures that the YAML schema files in contracts/ are valid
and can be loaded by Python libraries for runtime validation.
"""
import os
import sys
import yaml
from pathlib import Path

# Define the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

SCHEMA_FILES = [
    "dataset.schema.yaml",
    "model_output.schema.yaml",
    "evaluation_results.schema.yaml"
]

def validate_yaml_syntax(file_path: Path) -> bool:
    """Check if the YAML file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
        return True
    except yaml.YAMLError as e:
        print(f"YAML Error in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False

def check_required_keys(file_path: Path) -> bool:
    """Basic check for required top-level keys."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        print(f"Error: {file_path} is not a YAML object.")
        return False

    if "$schema" not in data:
        print(f"Warning: {file_path} missing $schema key.")

    if "title" not in data:
        print(f"Warning: {file_path} missing title key.")

    return True

def main():
    print(f"Validating contract schemas in {CONTRACTS_DIR}...")
    all_valid = True

    for schema_file in SCHEMA_FILES:
        file_path = CONTRACTS_DIR / schema_file
        if not file_path.exists():
            print(f"Error: {file_path} does not exist.")
            all_valid = False
            continue

        print(f"Checking {schema_file}...")

        # 1. Syntax Check
        if not validate_yaml_syntax(file_path):
            all_valid = False
            continue

        # 2. Structure Check
        if not check_required_keys(file_path):
            all_valid = False
            continue

        print(f"  -> {schema_file} is valid.")

    if all_valid:
        print("\nAll contract schemas are valid.")
        return 0
    else:
        print("\nSome contract schemas are invalid.")
        return 1

if __name__ == "__main__":
    sys.exit(main())