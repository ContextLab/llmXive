"""
Validator module for dataset configuration files.

This module provides functionality to validate JSON configuration files
against a YAML-defined schema for dataset sources (NCBI SRA, Zenodo).
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
import jsonschema

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset-config.schema.yaml"
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "data" / "config" / "dataset_ids.json"


def load_schema(schema_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the JSON schema from a YAML file.
    
    Args:
        schema_path: Path to the schema YAML file. Defaults to contracts/dataset-config.schema.yaml.
        
    Returns:
        Dict representing the loaded schema.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is not valid YAML.
    """
    if schema_path is None:
        schema_path = str(SCHEMA_PATH)
    else:
        schema_path = str(Path(schema_path))
        
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
        
    logger.info(f"Schema loaded successfully from {schema_path}")
    return schema


def validate_dataset_config(config_path: str) -> bool:
    """
    Validate a dataset configuration JSON file against the schema.
    
    This function loads a JSON configuration file and validates it against
    the schema defined in contracts/dataset-config.schema.yaml.
    
    Args:
        config_path: Path to the JSON configuration file to validate.
        
    Returns:
        bool: True if validation is successful.
        
    Raises:
        ValueError: If the configuration is invalid according to the schema.
        FileNotFoundError: If the configuration file does not exist.
        json.JSONDecodeError: If the configuration file is not valid JSON.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    # Load the schema
    schema = load_schema()
    
    # Load the configuration
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        
    # Validate
    try:
        jsonschema.validate(instance=config, schema=schema)
        logger.info(f"Configuration validation successful for {config_path}")
        return True
    except jsonschema.ValidationError as e:
        error_msg = f"Configuration validation failed: {e.message}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e
    except jsonschema.SchemaError as e:
        error_msg = f"Schema error during validation: {e.message}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e


def main():
    """
    Main entry point for standalone validation.
    
    Usage:
        python validators.py [config_path]
        
    If no config_path is provided, defaults to data/config/dataset_ids.json.
    """
    config_path = sys.argv[1] if len(sys.argv) > 1 else str(DEFAULT_CONFIG_PATH)
    
    try:
        is_valid = validate_dataset_config(config_path)
        if is_valid:
            print(f"✓ Configuration is valid: {config_path}")
            sys.exit(0)
    except FileNotFoundError as e:
        print(f"✗ File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"✗ Validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()