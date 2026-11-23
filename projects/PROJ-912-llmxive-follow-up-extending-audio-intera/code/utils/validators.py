"""
Schema validation utilities for contracts and data integrity.

This module provides robust validation functions for:
- Dictionary schemas (contract validation)
- Dataclass instances
- JSON files
- Model metadata structures
- Configuration sections

All validators raise SchemaValidationError on failure with detailed messages.
"""

import json
import re
from typing import Any, Dict, List, Optional, Type, Union
from dataclasses import is_dataclass, fields, MISSING
from pathlib import Path

from utils.logger import LlmXiveError, ConfigurationError, DataLoadError


class SchemaValidationError(LlmXiveError):
    """Raised when schema validation fails."""
    pass


def validate_dict_schema(
    data: Dict[str, Any],
    schema: Dict[str, Any],
    path: str = "root"
) -> bool:
    """
    Validate a dictionary against a schema definition.
    
    Args:
        data: The dictionary to validate
        schema: Schema definition where keys are field names and values are:
                - A type (e.g., str, int, list)
                - A dict with 'type' and optional 'required' keys
                - A callable that returns True if valid
        path: Current path in the structure for error messages
    
    Returns:
        True if validation passes
    
    Raises:
        SchemaValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise SchemaValidationError(f"{path}: Expected dict, got {type(data).__name__}")
    
    for field_name, field_spec in schema.items():
        field_path = f"{path}.{field_name}"
        
        # Check if field exists
        if field_name not in data:
            # Determine if required
            is_required = True
            if isinstance(field_spec, dict):
                is_required = field_spec.get('required', True)
            
            if is_required:
                raise SchemaValidationError(f"{field_path}: Missing required field")
            continue
        
        value = data[field_name]
        
        # Validate based on spec type
        if callable(field_spec):
            if not field_spec(value):
                raise SchemaValidationError(f"{field_path}: Custom validation failed")
        elif isinstance(field_spec, dict):
            expected_type = field_spec.get('type')
            if expected_type:
                if not isinstance(value, expected_type):
                    raise SchemaValidationError(
                        f"{field_path}: Expected {expected_type.__name__}, got {type(value).__name__}"
                    )
            
            # Nested schema validation
            if 'schema' in field_spec and isinstance(value, dict):
                validate_dict_schema(value, field_spec['schema'], field_path)
        elif isinstance(field_spec, type):
            if not isinstance(value, field_spec):
                raise SchemaValidationError(
                    f"{field_path}: Expected {field_spec.__name__}, got {type(value).__name__}"
                )
    
    return True


def validate_dataclass(instance: Any, schema: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate a dataclass instance against its type hints or an optional schema.
    
    Args:
        instance: The dataclass instance to validate
        schema: Optional schema override for field validation
    
    Returns:
        True if validation passes
    
    Raises:
        SchemaValidationError: If validation fails
    """
    if not is_dataclass(instance):
        raise SchemaValidationError(f"Not a dataclass instance: {type(instance).__name__}")
    
    for field_obj in fields(instance):
        field_name = field_obj.name
        value = getattr(instance, field_name)
        
        # Check for None on non-optional fields
        if value is None:
            if not field_obj.type is not type(None) and 'Optional' not in str(field_obj.type):
                # Check if it has a default
                if field_obj.default is MISSING and field_obj.default_factory is MISSING:
                    raise SchemaValidationError(f"{field_name}: None value on non-optional field")
        
        # Type checking if schema provided
        if schema and field_name in schema:
            field_spec = schema[field_name]
            if isinstance(field_spec, type):
                if not isinstance(value, field_spec):
                    raise SchemaValidationError(
                        f"{field_name}: Expected {field_spec.__name__}, got {type(value).__name__}"
                    )
    
    return True


def validate_json_file(
    file_path: Union[str, Path],
    schema: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate a JSON file against an optional schema.
    
    Args:
        file_path: Path to the JSON file
        schema: Optional schema for validation
    
    Returns:
        Parsed JSON data if valid
    
    Raises:
        SchemaValidationError: If file missing, invalid JSON, or schema mismatch
    """
    path = Path(file_path)
    
    if not path.exists():
        raise SchemaValidationError(f"File not found: {path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise SchemaValidationError(f"Invalid JSON in {path}: {str(e)}")
    except Exception as e:
        raise SchemaValidationError(f"Error reading {path}: {str(e)}")
    
    if schema:
        validate_dict_schema(data, schema, path=str(path))
    
    return data


def validate_model_metadata(metadata: Dict[str, Any]) -> bool:
    """
    Validate model metadata structure.
    
    Expected schema:
    {
        "model_id": str,
        "bit_width": int,
        "pruning_ratio": float,
        "param_count": int,
        "compression_type": str,
        "teacher_id": str,
        "training_loss": float
    }
    
    Args:
        metadata: The metadata dictionary to validate
    
    Returns:
        True if valid
    
    Raises:
        SchemaValidationError: If validation fails
    """
    schema = {
        'model_id': str,
        'bit_width': int,
        'pruning_ratio': float,
        'param_count': int,
        'compression_type': str,
        'teacher_id': str,
        'training_loss': float
    }
    
    return validate_dict_schema(metadata, schema)


def validate_config_section(
    config_data: Dict[str, Any],
    section_name: str,
    required_fields: List[str],
    type_hints: Optional[Dict[str, Type]] = None
) -> bool:
    """
    Validate a specific section of a configuration.
    
    Args:
        config_data: The full configuration dictionary
        section_name: The key of the section to validate
        required_fields: List of required field names within the section
        type_hints: Optional dict mapping field names to expected types
    
    Returns:
        True if valid
    
    Raises:
        SchemaValidationError: If validation fails
    """
    if section_name not in config_data:
        raise SchemaValidationError(f"Missing config section: {section_name}")
    
    section = config_data[section_name]
    
    if not isinstance(section, dict):
        raise SchemaValidationError(f"Config section '{section_name}' must be a dict")
    
    # Check required fields
    for field in required_fields:
        if field not in section:
            raise SchemaValidationError(f"Missing required field '{field}' in section '{section_name}'")
    
    # Check types if provided
    if type_hints:
        for field, expected_type in type_hints.items():
            if field in section:
                if not isinstance(section[field], expected_type):
                    raise SchemaValidationError(
                        f"Field '{field}' in section '{section_name}': "
                        f"Expected {expected_type.__name__}, got {type(section[field]).__name__}"
                    )
    
    return True


def validate_audio_manifest(manifest: Dict[str, Any]) -> bool:
    """
    Validate an audio manifest structure.
    
    Expected schema:
    {
        "files": List[Dict[str, Any]],
        "class_map": Dict[int, str],
        "metadata": Dict[str, Any]
    }
    
    Args:
        manifest: The manifest dictionary
    
    Returns:
        True if valid
    
    Raises:
        SchemaValidationError: If validation fails
    """
    schema = {
        'files': list,
        'class_map': dict,
        'metadata': dict
    }
    
    validate_dict_schema(manifest, schema)
    
    # Validate class_map keys are integers
    for key in manifest['class_map'].keys():
        if not isinstance(key, int):
            raise SchemaValidationError(f"class_map keys must be integers, found {type(key).__name__}")
    
    # Validate files structure
    for idx, file_entry in enumerate(manifest['files']):
        if not isinstance(file_entry, dict):
            raise SchemaValidationError(f"files[{idx}] must be a dict")
        if 'path' not in file_entry:
            raise SchemaValidationError(f"files[{idx}] missing 'path' field")
        if 'class_id' not in file_entry:
            raise SchemaValidationError(f"files[{idx}] missing 'class_id' field")
    
    return True


def validate_metrics_csv_header(headers: List[str]) -> bool:
    """
    Validate the header row of a metrics CSV file.
    
    Required columns: model_id, auc, latency_ms, ram_gb
    
    Args:
        headers: List of header strings
    
    Returns:
        True if valid
    
    Raises:
        SchemaValidationError: If validation fails
    """
    required = {'model_id', 'auc', 'latency_ms', 'ram_gb'}
    header_set = set(h.strip().lower() for h in headers)
    
    missing = required - header_set
    if missing:
        raise SchemaValidationError(f"Missing required CSV columns: {missing}")
    
    return True


def validate_breaking_point_json(data: Dict[str, Any]) -> bool:
    """
    Validate the breaking point JSON structure.
    
    Expected schema:
    {
        "bit_width": int,
        "drop_percent": float,
        "threshold_violated": bool,
        "model_id": str
    }
    
    Args:
        data: The breaking point data
    
    Returns:
        True if valid
    
    Raises:
        SchemaValidationError: If validation fails
    """
    schema = {
        'bit_width': int,
        'drop_percent': float,
        'threshold_violated': bool,
        'model_id': str
    }
    
    return validate_dict_schema(data, schema)


def validate_ablation_config(config: Dict[str, Any]) -> bool:
    """
    Validate an ablation configuration.
    
    Expected schema:
    {
        "freeze_heads": List[int],
        "prune_ffn_layers": List[int]
    }
    
    Args:
        config: The ablation config
    
    Returns:
        True if valid
    
    Raises:
        SchemaValidationError: If validation fails
    """
    schema = {
        'freeze_heads': list,
        'prune_ffn_layers': list
    }
    
    validate_dict_schema(config, schema)
    
    # Validate lists contain only integers
    for head in config.get('freeze_heads', []):
        if not isinstance(head, int):
            raise SchemaValidationError("freeze_heads must contain only integers")
    
    for layer in config.get('prune_ffn_layers', []):
        if not isinstance(layer, int):
            raise SchemaValidationError("prune_ffn_layers must contain only integers")
    
    return True