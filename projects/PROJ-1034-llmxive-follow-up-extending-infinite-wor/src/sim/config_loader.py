"""
Configuration loader for the CA Engine.
Validates and loads the YAML schema defined in config_schema.yaml.
"""
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

# Define the path to the schema file relative to this module
_SCHEMA_PATH = Path(__file__).parent / "config_schema.yaml"

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads and validates the CA engine configuration.

    If config_path is provided, it loads from that file.
    Otherwise, it loads the default configuration from config_schema.yaml.

    Args:
        config_path: Optional path to a custom configuration YAML file.

    Returns:
        Dict containing the validated configuration.

    Raises:
        FileNotFoundError: If the specified config file does not exist.
        yaml.YAMLError: If the YAML file is malformed.
        ValueError: If the configuration does not match the expected schema structure.
    """
    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    else:
        # Load default schema config
        if not _SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Default schema file not found: {_SCHEMA_PATH}")
        with open(_SCHEMA_PATH, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            # The default config is stored under the 'config' key in the schema file
            config = data.get('config', {})

    # Basic structural validation (deep validation logic can be expanded with jsonschema if needed)
    required_keys = ['engine', 'locality', 'memory', 'non_linearity', 'simulation']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration section: {key}")

    return config

def validate_schema() -> bool:
    """
    Validates that the default schema file loads without error.
    This is used for T004a verification.

    Returns:
        True if the schema loads successfully.

    Raises:
        Exception: If the schema fails to load or is invalid.
    """
    try:
        with open(_SCHEMA_PATH, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Verify the schema structure exists
        if 'schema' not in data:
            raise ValueError("Schema file missing 'schema' definition")
        
        # Verify the default config exists and matches basic structure
        if 'config' not in data:
            raise ValueError("Schema file missing 'config' default instance")
        
        config = data['config']
        required_keys = ['engine', 'locality', 'memory', 'non_linearity', 'simulation']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Default config missing required section: {key}")

        return True
    except yaml.YAMLError as e:
        raise RuntimeError(f"YAML parsing error in schema file: {e}")
    except Exception as e:
        raise RuntimeError(f"Schema validation failed: {e}")
