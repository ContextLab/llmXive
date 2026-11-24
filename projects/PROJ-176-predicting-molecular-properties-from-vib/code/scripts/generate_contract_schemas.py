"""
Helper script to validate contract schemas.
"""
import os
import sys
import yaml
import json
from pathlib import Path
from typing import List, Dict, Any

def validate_yaml_syntax(file_path: Path) -> bool:
    """Validate that a YAML file has correct syntax."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            yaml.safe_load(f)
        return True
    except yaml.YAMLError as e:
        print(f"YAML syntax error in {file_path}: {e}")
        return False

def check_required_keys(schema: Dict[str, Any], required_keys: List[str]) -> bool:
    """Check if a schema dictionary contains all required keys."""
    missing = [k for k in required_keys if k not in schema]
    if missing:
        print(f"Missing required keys in schema: {missing}")
        return False
    return True

def validate_schema_integrity(schema_path: Path) -> bool:
    """Validate the integrity of a schema file."""
    if not schema_path.is_file():
        print(f"Schema file not found: {schema_path}")
        return False
    if not validate_yaml_syntax(schema_path):
        return False
    # Example required keys – adjust as needed per project conventions
    required = ["type", "properties"]
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    return check_required_keys(schema, required)

def main():
    """Validate all schemas under specs/*/contracts."""
    base_dir = Path("specs")
    for contract_file in base_dir.rglob("*.schema.yaml"):
        print(f"Validating {contract_file}")
        if not validate_schema_integrity(contract_file):
            sys.exit(1)
    print("All contract schemas are valid.")

if __name__ == "__main__":
    main()