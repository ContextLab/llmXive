import os
import sys
import yaml
import json
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path if running as script
if 'code' not in sys.path[0]:
    code_dir = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(code_dir))

def validate_yaml_syntax(file_path: Path) -> bool:
    """Validate that a YAML file has correct syntax."""
    try:
        with open(file_path, 'r') as f:
            yaml.safe_load(f)
        return True
    except yaml.YAMLError as e:
        print(f"YAML Syntax Error in {file_path}: {e}")
        return False

def check_required_keys(schema: Dict[str, Any], required_keys: List[str]) -> bool:
    """Check if a schema dictionary contains all required keys."""
    missing = [key for key in required_keys if key not in schema]
    if missing:
        print(f"Missing required keys: {missing}")
        return False
    return True

def validate_schema_integrity(schema_path: Path) -> bool:
    """Validate the integrity of a schema file."""
    if not validate_yaml_syntax(schema_path):
        return False
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Basic structural checks
    required_top_level = ['schema_version', 'description', 'type', 'properties']
    if not check_required_keys(schema, required_top_level):
        print(f"Schema {schema_path} missing top-level keys")
        return False
    
    # Check for 'required' field at root if type is object
    if schema.get('type') == 'object' and 'required' not in schema:
        # Not strictly an error, but a warning
        print(f"Warning: Schema {schema_path} is an object but has no 'required' list")
    
    return True

def main():
    """Main entry point for schema validation."""
    contracts_dir = Path(__file__).resolve().parent.parent.parent / 'contracts'
    
    if not contracts_dir.exists():
        print(f"Contracts directory not found: {contracts_dir}")
        return 1
    
    schema_files = [
        contracts_dir / 'dataset.schema.yaml',
        contracts_dir / 'model_output.schema.yaml',
        contracts_dir / 'evaluation_results.schema.yaml'
    ]
    
    all_valid = True
    for schema_file in schema_files:
        print(f"Validating {schema_file.name}...")
        if not validate_schema_integrity(schema_file):
            all_valid = False
        else:
            print(f"  ✓ {schema_file.name} is valid")
    
    if all_valid:
        print("\nAll schema files are valid.")
        return 0
    else:
        print("\nSome schema files failed validation.")
        return 1

if __name__ == '__main__':
    sys.exit(main())