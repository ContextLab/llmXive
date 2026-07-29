"""
code/validators.py
Validates dataset configuration against schema and URL patterns.
"""
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
import jsonschema

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Hardcoded URL patterns
VALID_SRA = re.compile(r'^(SRR|ERR)[0-9]+$')
VALID_ZENDO = re.compile(r'^10\.5281/zenodo\.[0-9]+$')

# Inline Schema Definition
SCHEMA = {
    "type": "object",
    "properties": {
        "datasets": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "source": {"type": "string", "enum": ["NCBI_SRA", "Zenodo"]},
                    "url": {"type": "string"}
                },
                "required": ["id", "source", "url"]
            }
        }
    },
    "required": ["datasets"]
}

def load_schema(schema_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the schema from a file or return the inline schema.
    """
    if schema_path and os.path.exists(schema_path):
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    return SCHEMA

def validate_dataset_config(config_path: str) -> bool:
    """
    Validate the dataset configuration file.
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return False

    schema = load_schema()
    
    try:
        jsonschema.validate(instance=config, schema=schema)
    except jsonschema.ValidationError as e:
        logger.error(f"Schema validation failed: {e.message}")
        return False

    # Check URL patterns
    for dataset in config.get('datasets', []):
        source = dataset.get('source')
        id_val = dataset.get('id')
        url_val = dataset.get('url')

        if source == "NCBI_SRA":
            if not VALID_SRA.match(id_val):
                logger.error(f"Invalid SRA ID: {id_val}")
                return False
        elif source == "Zenodo":
            if not VALID_ZENDO.match(url_val):
                logger.error(f"Invalid Zenodo URL: {url_val}")
                return False

    return True

def main():
    # Example usage for testing
    config_path = "data/config/dataset_ids.json"
    if validate_dataset_config(config_path):
        print("Validation passed")
    else:
        print("Validation failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
