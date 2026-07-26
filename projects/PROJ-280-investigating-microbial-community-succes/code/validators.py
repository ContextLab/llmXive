import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
import jsonschema

logger = logging.getLogger(__name__)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load JSON schema from YAML file."""
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    return schema

def validate_dataset_config(config_path: str) -> bool:
    """
    Validate dataset config JSON against schema.
    Raises ValueError if invalid.
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # Determine schema path relative to project root
    # Assuming script runs from project root or we resolve relative to config
    # The config is at data/config/dataset_ids.json
    # The schema should be at contracts/dataset-config.schema.yaml
    # We resolve relative to the config file's parent's parent (project root)
    project_root = config_path.parent.parent
    schema_path = project_root / "contracts" / "dataset-config.schema.yaml"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    schema = load_schema(str(schema_path))

    with open(config_path, 'r') as f:
        config = json.load(f)

    try:
        jsonschema.validate(instance=config, schema=schema)
        logger.info(f"Dataset config validated successfully: {config_path}")
        return True
    except jsonschema.ValidationError as e:
        raise ValueError(f"Dataset config validation failed: {e.message}")

def main():
    config_path = "projects/PROJ-280-investigating-microbial-community-succes/data/config/dataset_ids.json"
    try:
        validate_dataset_config(config_path)
        print("Validation successful")
    except (ValueError, FileNotFoundError) as e:
        print(f"Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()