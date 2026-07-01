"""
Validation utilities to enforce contract schemas on generated and processed data.

This module provides functions to validate data against JSON Schema definitions
stored in the contracts/ directory. It ensures that simulation configurations,
estimation results, and aggregated metrics conform to the project's data contracts.
"""
import json
import os
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

import jsonschema
from jsonschema import validate, ValidationError, Draft7Validator

# Contract file paths relative to project root
CONTRACTS_DIR = Path("contracts")
SIMULATION_CONFIG_SCHEMA = CONTRACTS_DIR / "simulation_config.schema.yaml"
ESTIMATION_RESULT_SCHEMA = CONTRACTS_DIR / "estimation_result.schema.yaml"
AGGREGATED_METRIC_SCHEMA = CONTRACTS_DIR / "aggregated_metric.schema.yaml"

# Cache for loaded schemas to avoid repeated file I/O
_schema_cache: Dict[str, Dict[str, Any]] = {}


def _load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load a JSON Schema from a YAML or JSON file.
    
    Args:
        schema_path: Path to the schema file.
        
    Returns:
        The loaded schema as a dictionary.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        json.JSONDecodeError: If the file is not valid JSON (when expected).
    """
    cache_key = str(schema_path)
    if cache_key in _schema_cache:
        return _schema_cache[cache_key]
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    # Determine file type and load
    if schema_path.suffix.lower() in ['.yaml', '.yml']:
        try:
            import yaml
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = yaml.safe_load(f)
        except ImportError:
            raise ImportError("PyYAML is required to load YAML schemas. Install with: pip install pyyaml")
    elif schema_path.suffix.lower() == '.json':
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    else:
        raise ValueError(f"Unsupported schema file format: {schema_path.suffix}")
    
    _schema_cache[cache_key] = schema
    return schema


def validate_simulation_config(data: Dict[str, Any], strict: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Validate simulation configuration data against the contract schema.
    
    Args:
        data: Dictionary containing simulation configuration parameters.
        strict: If True, raises an exception on validation failure. 
               If False, returns (False, error_message).
               
    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
        
    Raises:
        FileNotFoundError: If the schema file is missing.
        ValidationError: If strict=True and validation fails.
    """
    try:
        schema = _load_schema(SIMULATION_CONFIG_SCHEMA)
        validate(instance=data, schema=schema)
        return True, None
    except ValidationError as e:
        error_msg = f"Simulation config validation failed: {e.message}"
        if strict:
            raise ValidationError(error_msg, path=e.absolute_path)
        return False, error_msg


def validate_estimation_result(data: Dict[str, Any], strict: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Validate estimation result data against the contract schema.
    
    Args:
        data: Dictionary containing estimation result parameters.
        strict: If True, raises an exception on validation failure.
               If False, returns (False, error_message).
               
    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
        
    Raises:
        FileNotFoundError: If the schema file is missing.
        ValidationError: If strict=True and validation fails.
    """
    try:
        schema = _load_schema(ESTIMATION_RESULT_SCHEMA)
        validate(instance=data, schema=schema)
        return True, None
    except ValidationError as e:
        error_msg = f"Estimation result validation failed: {e.message}"
        if strict:
            raise ValidationError(error_msg, path=e.absolute_path)
        return False, error_msg


def validate_aggregated_metric(data: Dict[str, Any], strict: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Validate aggregated metric data against the contract schema.
    
    Args:
        data: Dictionary containing aggregated metric parameters.
        strict: If True, raises an exception on validation failure.
               If False, returns (False, error_message).
               
    Returns:
        Tuple of (is_valid, error_message). error_message is None if valid.
        
    Raises:
        FileNotFoundError: If the schema file is missing.
        ValidationError: If strict=True and validation fails.
    """
    try:
        schema = _load_schema(AGGREGATED_METRIC_SCHEMA)
        validate(instance=data, schema=schema)
        return True, None
    except ValidationError as e:
        error_msg = f"Aggregated metric validation failed: {e.message}"
        if strict:
            raise ValidationError(error_msg, path=e.absolute_path)
        return False, error_msg


def validate_batch(
    data_list: List[Dict[str, Any]],
    validator_func,
    batch_name: str = "batch"
) -> List[Tuple[int, bool, Optional[str]]]:
    """
    Validate a batch of data items using a specific validator function.
    
    Args:
        data_list: List of dictionaries to validate.
        validator_func: A validator function that takes (data, strict=False) 
                       and returns (bool, str|None).
        batch_name: Name for the batch for logging purposes.
        
    Returns:
        List of tuples (index, is_valid, error_message) for each item.
    """
    results = []
    for i, data in enumerate(data_list):
        is_valid, error_msg = validator_func(data, strict=False)
        results.append((i, is_valid, error_msg))
    
    failed_count = sum(1 for _, is_valid, _ in results if not is_valid)
    if failed_count > 0:
        print(f"Validation warning for {batch_name}: {failed_count}/{len(data_list)} items failed.")
    
    return results


def get_validator(schema_path: Path) -> Draft7Validator:
    """
    Get a pre-compiled validator instance for a schema.
    
    Useful for validating multiple items against the same schema efficiently.
    
    Args:
        schema_path: Path to the schema file.
        
    Returns:
        A Draft7Validator instance.
    """
    schema = _load_schema(schema_path)
    return Draft7Validator(schema)