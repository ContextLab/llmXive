import json
import yaml
import os
import sys
import logging
from pathlib import Path
from typing import Any, Dict

def load_json_schema(json_path: str) -> Dict[str, Any]:
    """Load a JSON schema file and return its content as a dictionary."""
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"JSON schema file not found: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_yaml_schema(data: Dict[str, Any], yaml_path: str) -> None:
    """Save a dictionary as a YAML file."""
    # Ensure the directory exists
    yaml_dir = os.path.dirname(yaml_path)
    if yaml_dir:
        os.makedirs(yaml_dir, exist_ok=True)
    
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def convert_json_to_yaml(json_path: str, yaml_path: str) -> str:
    """Convert a JSON schema file to YAML format."""
    logging.info(f"Converting JSON schema from {json_path} to YAML: {yaml_path}")
    
    # Load JSON schema
    schema_data = load_json_schema(json_path)
    
    # Save as YAML
    save_yaml_schema(schema_data, yaml_path)
    
    logging.info(f"Successfully converted JSON schema to YAML: {yaml_path}")
    return yaml_path

def main():
    """Main entry point for the schema converter."""
    # Default paths relative to project root
    project_root = Path(__file__).resolve().parents[2]
    json_path = project_root / "contracts" / "dataset.schema.json"
    yaml_path = project_root / "contracts" / "dataset.schema.yaml"

    # Allow command-line overrides
    if len(sys.argv) >= 3:
        json_path = Path(sys.argv[1])
        yaml_path = Path(sys.argv[2])

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        output_path = convert_json_to_yaml(str(json_path), str(yaml_path))
        print(f"Conversion complete. YAML schema saved to: {output_path}")
        return 0
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        print(f"Error: {e}")
        return 1
    except Exception as e:
        logging.error(f"Conversion failed: {e}")
        print(f"Error during conversion: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
