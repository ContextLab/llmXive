"""
Schema validation utilities for llmXive pipeline.

Implements FR-002: Schema validation for data artifacts.
Handles edge cases with strict type checking and clear error messages.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import is_dataclass, fields


class ValidationError(Exception):
    """Custom exception for schema validation errors."""
    def __init__(self, message: str, path: Optional[str] = None, line: Optional[int] = None):
        self.message = message
        self.path = path
        self.line = line
        location = ""
        if path:
            location += f" in {path}"
        if line is not None:
            location += f" at line {line}"
        super().__init__(f"ValidationError:{location}: {message}")


def validate_schema(
    data: Dict[str, Any],
    schema: Dict[str, Any],
    path: str = "root"
) -> None:
    """
    Validate a dictionary against a schema definition.
    
    Args:
        data: The data dictionary to validate.
        schema: Schema definition with 'type' and optional 'properties'.
        path: Current path in the data structure for error reporting.
    
    Raises:
        ValidationError: If validation fails.
    """
    expected_type = schema.get("type")
    
    # Type checking
    if expected_type == "object":
        if not isinstance(data, dict):
            raise ValidationError(f"Expected object, got {type(data).__name__}", path)
        
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # Check required fields
        for field in required:
            if field not in data:
                raise ValidationError(f"Missing required field: '{field}'", path)
        
        # Validate each property
        for key, value in data.items():
            if key in properties:
                validate_schema(value, properties[key], f"{path}.{key}")
    
    elif expected_type == "array":
        if not isinstance(data, list):
            raise ValidationError(f"Expected array, got {type(data).__name__}", path)
        
        items_schema = schema.get("items")
        if items_schema:
            for idx, item in enumerate(data):
                validate_schema(item, items_schema, f"{path}[{idx}]")
    
    elif expected_type == "string":
        if not isinstance(data, str):
            raise ValidationError(f"Expected string, got {type(data).__name__}", path)
    
    elif expected_type == "integer":
        if not isinstance(data, int) or isinstance(data, bool):
            raise ValidationError(f"Expected integer, got {type(data).__name__}", path)
    
    elif expected_type == "number":
        if not isinstance(data, (int, float)) or isinstance(data, bool):
            raise ValidationError(f"Expected number, got {type(data).__name__}", path)
    
    elif expected_type == "boolean":
        if not isinstance(data, bool):
            raise ValidationError(f"Expected boolean, got {type(data).__name__}", path)
    
    elif expected_type == "null":
        if data is not None:
            raise ValidationError(f"Expected null, got {type(data).__name__}", path)


def validate_jsonl_file(
    file_path: Union[str, Path],
    schema: Dict[str, Any]
) -> Tuple[int, List[str]]:
    """
    Validate a JSONL file against a schema.
    
    Args:
        file_path: Path to the JSONL file.
        schema: Schema definition for each line.
    
    Returns:
        Tuple of (valid_count, list of error messages).
    
    Raises:
        ValidationError: If the file cannot be read or is completely invalid.
    """
    path = str(file_path)
    if not os.path.exists(path):
        raise ValidationError(f"File not found: {path}")
    
    valid_count = 0
    errors = []
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    validate_schema(data, schema, path=f"{path} line {line_num}")
                    valid_count += 1
                except json.JSONDecodeError as e:
                    errors.append(f"Line {line_num}: Invalid JSON - {str(e)}")
                except ValidationError as e:
                    errors.append(str(e))
    
    except IOError as e:
        raise ValidationError(f"Cannot read file: {path} - {str(e)}")
    
    return valid_count, errors


def validate_manifest_structure(manifest_path: Union[str, Path]) -> None:
    """
    Validate the structure of a manifest.jsonl file.
    
    Expected structure:
    {
        "chunks": [
            {
                "id": "string",
                "start_time": "number",
                "end_time": "number",
                "frame_count": "integer",
                "path": "string"
            }
        ],
        "metadata": {
            "total_duration": "number",
            "total_frames": "integer",
            "generated_at": "string"
        }
    }
    
    Args:
        manifest_path: Path to the manifest file.
    
    Raises:
        ValidationError: If structure is invalid.
    """
    path = str(manifest_path)
    
    if not os.path.exists(path):
        raise ValidationError(f"Manifest file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        try:
            manifest = json.load(f)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in manifest: {str(e)}", path)
    
    # Validate top-level keys
    if not isinstance(manifest, dict):
        raise ValidationError("Manifest must be a JSON object", path)
    
    if "chunks" not in manifest:
        raise ValidationError("Missing required field: 'chunks'", path)
    
    if "metadata" not in manifest:
        raise ValidationError("Missing required field: 'metadata'", path)
    
    # Validate chunks array
    chunks = manifest["chunks"]
    if not isinstance(chunks, list):
        raise ValidationError("'chunks' must be an array", path)
    
    for idx, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            raise ValidationError(f"Chunk {idx} must be an object", path)
        
        required_chunk_fields = ["id", "start_time", "end_time", "frame_count", "path"]
        for field in required_chunk_fields:
            if field not in chunk:
                raise ValidationError(f"Chunk {idx} missing required field: '{field}'", path)
        
        if not isinstance(chunk["id"], str):
            raise ValidationError(f"Chunk {idx} 'id' must be string", path)
        
        if not isinstance(chunk["start_time"], (int, float)):
            raise ValidationError(f"Chunk {idx} 'start_time' must be number", path)
        
        if not isinstance(chunk["end_time"], (int, float)):
            raise ValidationError(f"Chunk {idx} 'end_time' must be number", path)
        
        if not isinstance(chunk["frame_count"], int):
            raise ValidationError(f"Chunk {idx} 'frame_count' must be integer", path)
        
        if not isinstance(chunk["path"], str):
            raise ValidationError(f"Chunk {idx} 'path' must be string", path)
        
        if chunk["start_time"] > chunk["end_time"]:
            raise ValidationError(
                f"Chunk {idx} 'start_time' ({chunk['start_time']}) > 'end_time' ({chunk['end_time']})",
                path
            )
    
    # Validate metadata
    metadata = manifest["metadata"]
    if not isinstance(metadata, dict):
        raise ValidationError("'metadata' must be an object", path)
    
    if "total_duration" not in metadata:
        raise ValidationError("Missing required field: 'metadata.total_duration'", path)
    
    if "total_frames" not in metadata:
        raise ValidationError("Missing required field: 'metadata.total_frames'", path)
    
    if not isinstance(metadata["total_duration"], (int, float)):
        raise ValidationError("'metadata.total_duration' must be number", path)
    
    if not isinstance(metadata["total_frames"], int):
        raise ValidationError("'metadata.total_frames' must be integer", path)


def validate_dimension_match(
    actual_dim: int,
    expected_dim: int,
    dimension_name: str = "dimension",
    context: Optional[str] = None
) -> None:
    """
    Validate that an actual dimension matches an expected dimension.
    
    Args:
        actual_dim: The actual dimension size.
        expected_dim: The expected dimension size.
        dimension_name: Name of the dimension for error message.
        context: Optional context for the error message.
    
    Raises:
        ValidationError: If dimensions do not match.
    """
    if actual_dim != expected_dim:
        context_str = f" ({context})" if context else ""
        raise ValidationError(
            f"Dimension mismatch{context_str}: Expected {dimension_name}={expected_dim}, "
            f"Actual {dimension_name}={actual_dim}"
        )


def validate_feature_keys(
    feature_dict: Dict[str, Any],
    required_keys: List[str],
    optional_keys: Optional[List[str]] = None
) -> None:
    """
    Validate that a feature dictionary contains required keys.
    
    Args:
        feature_dict: The feature dictionary to validate.
        required_keys: List of required key names.
        optional_keys: Optional list of allowed extra keys.
    
    Raises:
        ValidationError: If required keys are missing or unexpected keys are present.
    """
    if not isinstance(feature_dict, dict):
        raise ValidationError(f"Feature data must be a dictionary, got {type(feature_dict).__name__}")
    
    # Check required keys
    missing_keys = [key for key in required_keys if key not in feature_dict]
    if missing_keys:
        raise ValidationError(f"Missing required feature keys: {', '.join(missing_keys)}")
    
    # Check for unexpected keys if optional_keys is provided
    if optional_keys is not None:
        allowed_keys = set(required_keys + optional_keys)
        unexpected_keys = [key for key in feature_dict.keys() if key not in allowed_keys]
        if unexpected_keys:
            raise ValidationError(f"Unexpected feature keys: {', '.join(unexpected_keys)}")


def validate_dataclass_instance(
    obj: Any,
    expected_type: type
) -> None:
    """
    Validate that an object is an instance of a dataclass with expected fields.
    
    Args:
        obj: The object to validate.
        expected_type: The expected dataclass type.
    
    Raises:
        ValidationError: If validation fails.
    """
    if not is_dataclass(obj):
        raise ValidationError(f"Object is not a dataclass instance: {type(obj).__name__}")
    
    if not isinstance(obj, expected_type):
        raise ValidationError(
            f"Expected dataclass type {expected_type.__name__}, "
            f"got {type(obj).__name__}"
        )
    
    expected_fields = {f.name for f in fields(expected_type)}
    actual_fields = {f.name for f in fields(obj)}
    
    missing_fields = expected_fields - actual_fields
    if missing_fields:
        raise ValidationError(f"Missing dataclass fields: {', '.join(missing_fields)}")