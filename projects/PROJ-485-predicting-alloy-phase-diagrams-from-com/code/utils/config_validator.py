"""
Configuration validation module for alloy phase diagram prediction pipeline.
Validates code/config.yaml against defined schema requirements.
"""
import os
import sys
import yaml
from typing import Dict, Any, List, Optional
from utils.logging import get_logger, log_error, log_info, log_warning
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

# Required top-level keys for configuration
REQUIRED_TOP_LEVEL_KEYS = [
    'nist_janaf_url',
    'sgte_url',
    'local_fallback_path',
    'data_schema'
]

# Required keys within data_schema
REQUIRED_SCHEMA_KEYS = [
    'required_columns'
]

# Required columns for phase boundary data (FR-001)
REQUIRED_PHASE_BOUNDARY_COLUMNS = [
    'temperature',
    'composition'
]

def validate_config(config_path: str = 'code/config.yaml') -> bool:
    """
    Validate the configuration file against the required schema.
    
    Args:
        config_path: Path to the YAML configuration file.
        
    Returns:
        True if validation passes, False otherwise.
        
    Raises:
        ValueError: If validation fails with specific error code.
    """
    logger.info(f"Validating configuration file: {config_path}")
    
    if not os.path.exists(config_path):
        log_error(ErrorCode.DATA_SOURCE_MISSING, f"Configuration file not found: {config_path}")
        raise ValueError(f"{ErrorCode.DATA_SOURCE_MISSING.value}: Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        log_error(ErrorCode.INVALID_DATA_SCHEMA, f"Failed to parse YAML: {e}")
        raise ValueError(f"{ErrorCode.INVALID_DATA_SCHEMA.value}: Failed to parse YAML: {e}")
    
    if not isinstance(config, dict):
        log_error(ErrorCode.INVALID_DATA_SCHEMA, "Configuration must be a YAML mapping")
        raise ValueError(f"{ErrorCode.INVALID_DATA_SCHEMA.value}: Configuration must be a YAML mapping")
    
    # Check required top-level keys
    missing_keys = []
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in config:
            missing_keys.append(key)
    
    if missing_keys:
        error_msg = f"Missing required configuration keys: {', '.join(missing_keys)}"
        log_error(ErrorCode.INVALID_DATA_SCHEMA, error_msg)
        raise ValueError(f"{ErrorCode.INVALID_DATA_SCHEMA.value}: {error_msg}")
    
    # Check for empty URL fields
    url_keys = ['nist_janaf_url', 'sgte_url', 'local_fallback_path']
    for key in url_keys:
        if not config[key] or not config[key].strip():
            error_msg = f"Configuration key '{key}' cannot be empty"
            log_error(ErrorCode.DATA_SOURCE_MISSING, error_msg)
            raise ValueError(f"{ErrorCode.DATA_SOURCE_MISSING.value}: {error_msg}")
    
    # Validate data_schema section
    data_schema = config.get('data_schema', {})
    if not isinstance(data_schema, dict):
        error_msg = "data_schema must be a mapping"
        log_error(ErrorCode.INVALID_DATA_SCHEMA, error_msg)
        raise ValueError(f"{ErrorCode.INVALID_DATA_SCHEMA.value}: {error_msg}")
    
    # Check required schema keys
    missing_schema_keys = []
    for key in REQUIRED_SCHEMA_KEYS:
        if key not in data_schema:
            missing_schema_keys.append(key)
    
    if missing_schema_keys:
        error_msg = f"Missing required data_schema keys: {', '.join(missing_schema_keys)}"
        log_error(ErrorCode.INVALID_DATA_SCHEMA, error_msg)
        raise ValueError(f"{ErrorCode.INVALID_DATA_SCHEMA.value}: {error_msg}")
    
    # Validate required_columns
    required_columns = data_schema.get('required_columns', [])
    if not isinstance(required_columns, list):
        error_msg = "required_columns must be a list"
        log_error(ErrorCode.INVALID_DATA_SCHEMA, error_msg)
        raise ValueError(f"{ErrorCode.INVALID_DATA_SCHEMA.value}: {error_msg}")
    
    # FR-001: Explicitly require phase boundary coordinates (temperature, composition)
    missing_boundary_cols = []
    for col in REQUIRED_PHASE_BOUNDARY_COLUMNS:
        if col not in required_columns:
            missing_boundary_cols.append(col)
    
    if missing_boundary_cols:
        error_msg = f"Phase boundary coordinates missing from required_columns: {', '.join(missing_boundary_cols)}. FR-001 requires temperature and composition."
        log_error(ErrorCode.INVALID_DATA_SCHEMA, error_msg)
        raise ValueError(f"{ErrorCode.INVALID_DATA_SCHEMA.value}: {error_msg}")
    
    # Validate optional validation rules if present
    validation_rules = data_schema.get('validation_rules', {})
    if validation_rules:
        if not isinstance(validation_rules, dict):
            error_msg = "validation_rules must be a mapping"
            log_error(ErrorCode.INVALID_DATA_SCHEMA, error_msg)
            raise ValueError(f"{ErrorCode.INVALID_DATA_SCHEMA.value}: {error_msg}")
        
        log_info(f"Found validation rules: {list(validation_rules.keys())}")
    
    log_info("Configuration validation passed successfully")
    return True

def main():
    """Main entry point for configuration validation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate alloy phase diagram pipeline configuration')
    parser.add_argument(
        '--config', 
        type=str, 
        default='code/config.yaml',
        help='Path to configuration file (default: code/config.yaml)'
    )
    
    args = parser.parse_args()
    
    try:
        validate_config(args.config)
        print(f"Configuration validation PASSED for: {args.config}")
        sys.exit(0)
    except ValueError as e:
        print(f"Configuration validation FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        log_error(ErrorCode.RESOURCE_LIMIT_EXCEEDED, f"Unexpected error during validation: {e}")
        print(f"Unexpected error: {e}")
        sys.exit(2)

if __name__ == '__main__':
    main()