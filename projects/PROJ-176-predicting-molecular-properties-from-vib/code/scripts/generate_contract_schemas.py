"""
Script to validate and generate contract schemas for the project.
This script ensures that the schema files in contracts/ are valid YAML
and contain required keys.
"""
import os
import sys
import yaml
import json
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

REQUIRED_SCHEMAS = [
    "dataset.schema.yaml",
    "model_output.schema.yaml",
    "evaluation_results.schema.yaml"
]

def validate_yaml_syntax(file_path: Path) -> bool:
    """Validate that a YAML file has correct syntax."""
    try:
        with open(file_path, 'r') as f:
            yaml.safe_load(f)
        return True
    except yaml.YAMLError as e:
        print(f"YAML Error in {file_path}: {e}")
        return False

def check_required_keys(file_path: Path, required_keys: List[str]) -> bool:
    """Check if a YAML file contains all required top-level keys."""
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        missing_keys = []
        for key in required_keys:
            if key not in data:
                missing_keys.append(key)
        
        if missing_keys:
            print(f"Missing keys in {file_path}: {missing_keys}")
            return False
        return True
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False

def validate_schema_integrity(schema_path: Path) -> bool:
    """Perform basic integrity checks on a schema file."""
    if not schema_path.exists():
        print(f"Schema file missing: {schema_path}")
        return False
    
    if not validate_yaml_syntax(schema_path):
        return False
    
    # Load and check for basic structure
    with open(schema_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Check for schema version
    if 'schema_version' not in data:
        print(f"Missing schema_version in {schema_path}")
        return False
    
    # Check for artifact type
    if 'artifact_type' not in data:
        print(f"Missing artifact_type in {schema_path}")
        return False
    
    return True

def main():
    """Main entry point for schema validation."""
    print("Validating contract schemas...")
    
    all_valid = True
    
    for schema_name in REQUIRED_SCHEMAS:
        schema_path = CONTRACTS_DIR / schema_name
        print(f"\nChecking {schema_name}...")
        
        if not validate_schema_integrity(schema_path):
            all_valid = False
            continue
        
        print(f"  ✓ {schema_name} is valid")
    
    if all_valid:
        print("\n✓ All contract schemas are valid.")
        return 0
    else:
        print("\n✗ Some contract schemas are invalid.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
