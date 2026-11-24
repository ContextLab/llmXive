import yaml
import sys
from pathlib import Path

def validate_yaml(file_path: str):
    """Validates that a file is a syntactically correct YAML file."""
    print(f"Validating {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
        print(f"Successfully validated {file_path}")
    except Exception as e:
        print(f"Error validating {file_path}: {e}")
        sys.exit(1)

def main():
    # Paths relative to project root
    schemas = [
        "contracts/dataset.schema.yaml",
        "contracts/output.schema.yaml"
    ]
    
    for schema_path in schemas:
        if not Path(schema_path).exists():
            print(f"File not found: {schema_path}")
            sys.exit(1)
        validate_yaml(schema_path)
    
    print("All JSON-Schema contracts validated successfully.")

if __name__ == "__main__":
    main()