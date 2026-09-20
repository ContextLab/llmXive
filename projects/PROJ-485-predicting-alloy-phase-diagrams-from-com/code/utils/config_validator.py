"""
Configuration validator for T009b.
Validates code/config.yaml against the schema defined in T009a.
Ensures required keys exist and are non-empty.
"""
import os
import sys
import yaml
from typing import Dict, Any, List

# Add project root to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging import get_logger, log_error, log_info, log_warning
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")

REQUIRED_TOP_KEYS = [
    "nist_janaf_url",
    "sgte_url",
    "local_fallback_path"
]

REQUIRED_SCHEMA_KEYS = [
    "temperature",
    "composition",
    "element_a",
    "element_b"
]

def validate_config(config_path: str = None) -> bool:
    """
    Validates the configuration file.
    
    Returns True if valid, raises ValueError (with error code) if invalid.
    """
    path = config_path or CONFIG_PATH
    
    if not os.path.exists(path):
        logger.error(f"Configuration file not found: {path}", code=ErrorCode.DATA_SOURCE_MISSING)
        raise FileNotFoundError(f"Config file missing: {path}")

    try:
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML syntax in {path}: {e}", code=ErrorCode.INVALID_DATA_SCHEMA)
        raise ValueError(f"Invalid YAML syntax: {e}")

    if not isinstance(config, dict):
        logger.error("Config file must contain a top-level mapping", code=ErrorCode.INVALID_DATA_SCHEMA)
        raise ValueError("Config file must contain a top-level mapping")

    # Check top-level keys
    missing_top_keys = [key for key in REQUIRED_TOP_KEYS if key not in config]
    if missing_top_keys:
        logger.error(f"Missing required top-level keys: {missing_top_keys}", code=ErrorCode.DATA_SOURCE_MISSING)
        raise ValueError(f"Missing required top-level keys: {missing_top_keys}")

    # Check that top-level URL/Path values are not empty
    for key in REQUIRED_TOP_KEYS:
        value = config.get(key)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            logger.error(f"Required key '{key}' is empty or missing", code=ErrorCode.DATA_SOURCE_MISSING)
            raise ValueError(f"Required key '{key}' is empty or missing")

    # Check data_schema
    if "data_schema" not in config:
        logger.error("Missing 'data_schema' section", code=ErrorCode.INVALID_DATA_SCHEMA)
        raise ValueError("Missing 'data_schema' section")

    data_schema = config["data_schema"]
    if "required_columns" not in data_schema:
        logger.error("Missing 'required_columns' in data_schema", code=ErrorCode.INVALID_DATA_SCHEMA)
        raise ValueError("Missing 'required_columns' in data_schema")

    required_cols = data_schema["required_columns"]
    missing_schema_cols = [col for col in REQUIRED_SCHEMA_KEYS if col not in required_cols]
    if missing_schema_cols:
        logger.error(f"Missing required schema columns: {missing_schema_cols}", code=ErrorCode.INVALID_DATA_SCHEMA)
        raise ValueError(f"Missing required schema columns: {missing_schema_cols}")

    log_info("Configuration validation passed successfully.")
    return True

def main():
    """Entry point for CLI validation."""
    logger.info("Starting configuration validation...")
    try:
        validate_config()
        log_info("Validation successful. Exiting with code 0.")
        sys.exit(0)
    except (ValueError, FileNotFoundError) as e:
        log_error(f"Validation failed: {e}", code=ErrorCode.INVALID_DATA_SCHEMA)
        sys.exit(1)

if __name__ == "__main__":
    main()