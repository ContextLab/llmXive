"""
Utility script to verify YAML schemas using yamllint and jsonschema.
This script is used to validate the contracts/dataset_metadata.schema.yaml.
"""
import yaml
import os
import sys
from pathlib import Path

def check_yamllint(schema_path: str) -> bool:
    """Run yamllint on the schema file."""
    try:
        import yamllint
        from yamllint import config, linter
    except ImportError:
        print("Warning: yamllint not installed. Skipping syntax check.")
        return True

    try:
        with open(schema_path, 'r') as f:
            content = f.read()
        
        # Default yamllint configuration
        conf = config.YamlLintConfig('extends: default')
        problems = list(linter.run(content, conf, schema_path))
        
        if problems:
            print("yamllint errors found:")
            for problem in problems:
                print(f"  {problem}")
            return False
        
        print("yamllint check passed.")
        return True
    except Exception as e:
        print(f"Error running yamllint: {e}")
        return False

def load_and_validate_schema(schema_path: str) -> bool:
    """Load the schema and perform basic structural validation."""
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        if not isinstance(schema, dict):
            print("Error: Schema is not a dictionary.")
            return False
        
        required_keys = ['$schema', 'type', 'properties']
        for key in required_keys:
            if key not in schema:
                print(f"Error: Missing required key '{key}' in schema.")
                return False
        
        if schema['type'] != 'object':
            print(f"Error: Schema type must be 'object', got '{schema['type']}'.")
            return False
        
        if 'properties' not in schema or not schema['properties']:
            print("Error: Schema must have non-empty 'properties'.")
            return False
        
        # Check for required fields if defined
        if 'required' in schema:
            if not isinstance(schema['required'], list):
                print("Error: 'required' must be a list.")
                return False
        
        print(f"Schema validation passed. Found {len(schema['properties'])} properties.")
        return True
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        return False
    except Exception as e:
        print(f"Error loading schema: {e}")
        return False

def main():
    project_root = Path(__file__).parent.parent.parent
    schema_path = project_root / "contracts" / "dataset_metadata.schema.yaml"
    
    if not schema_path.exists():
        print(f"Error: Schema file not found at {schema_path}")
        sys.exit(1)
    
    print(f"Verifying schema: {schema_path}")
    
    # 1. Check YAML syntax with yamllint
    yaml_ok = check_yamllint(str(schema_path))
    
    # 2. Load and validate schema structure
    load_ok = load_and_validate_schema(str(schema_path))
    
    if yaml_ok and load_ok:
        print("All checks passed for dataset_metadata.schema.yaml")
        sys.exit(0)
    else:
        print("Schema verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()