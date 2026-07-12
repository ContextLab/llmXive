"""
Schema validation utilities for llmXive pipeline.

Implements strict schema validation for data artifacts to ensure
data integrity and catch edge cases early in the pipeline.

Provides:
- validate_schema: Generic schema validator with detailed error reporting
- validate_jsonl_schema: Validator for JSONL data streams
- ValidationError: Custom exception for schema violations
"""

import json
from typing import Any, Dict, List, Optional, Set, Union
from pathlib import Path


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
        
        super().__init__(f"Validation Error{location}: {message}")


def _check_type(value: Any, expected_type: type, field_name: str) -> None:
    """Check if value matches expected type, raising ValidationError if not."""
    if not isinstance(value, expected_type):
        actual_type = type(value).__name__
        expected_name = expected_type.__name__
        raise ValidationError(
            f"Field '{field_name}' expected type '{expected_name}', got '{actual_type}'"
        )


def _validate_field(
    field_name: str,
    value: Any,
    schema_def: Dict[str, Any],
    line: Optional[int] = None
) -> None:
    """Validate a single field against its schema definition."""
    
    # Check required type
    if "type" in schema_def:
        expected_type = schema_def["type"]
        if expected_type == "string":
            _check_type(value, str, field_name)
        elif expected_type == "integer":
            _check_type(value, int, field_name)
        elif expected_type == "number":
            if not isinstance(value, (int, float)):
                raise ValidationError(
                    f"Field '{field_name}' expected number, got {type(value).__name__}",
                    line=line
                )
        elif expected_type == "boolean":
            _check_type(value, bool, field_name)
        elif expected_type == "array":
            _check_type(value, list, field_name)
        elif expected_type == "object":
            _check_type(value, dict, field_name)
    
    # Check minimum value (for numbers)
    if "minimum" in schema_def and isinstance(value, (int, float)):
        if value < schema_def["minimum"]:
            raise ValidationError(
                f"Field '{field_name}' value {value} is below minimum {schema_def['minimum']}",
                line=line
            )
    
    # Check maximum value (for numbers)
    if "maximum" in schema_def and isinstance(value, (int, float)):
        if value > schema_def["maximum"]:
            raise ValidationError(
                f"Field '{field_name}' value {value} is above maximum {schema_def['maximum']}",
                line=line
            )
    
    # Check min length (for strings and arrays)
    if "min_length" in schema_def:
        if isinstance(value, (str, list)) and len(value) < schema_def["min_length"]:
            raise ValidationError(
                f"Field '{field_name}' length {len(value)} is below minimum {schema_def['min_length']}",
                line=line
            )
    
    # Check max length (for strings and arrays)
    if "max_length" in schema_def:
        if isinstance(value, (str, list)) and len(value) > schema_def["max_length"]:
            raise ValidationError(
                f"Field '{field_name}' length {len(value)} exceeds maximum {schema_def['max_length']}",
                line=line
            )
    
    # Check pattern (for strings)
    if "pattern" in schema_def and isinstance(value, str):
        import re
        if not re.match(schema_def["pattern"], value):
            raise ValidationError(
                f"Field '{field_name}' value '{value}' does not match pattern '{schema_def['pattern']}'",
                line=line
            )
    
    # Check enum (for any type)
    if "enum" in schema_def:
        if value not in schema_def["enum"]:
            raise ValidationError(
                f"Field '{field_name}' value '{value}' not in allowed values: {schema_def['enum']}",
                line=line
            )
    
    # Validate nested object properties
    if schema_def.get("type") == "object" and "properties" in schema_def and isinstance(value, dict):
        validate_schema(value, schema_def["properties"], line=line)
    
    # Validate array items
    if schema_def.get("type") == "array" and "items" in schema_def and isinstance(value, list):
        for idx, item in enumerate(value):
            _validate_field(f"{field_name}[{idx}]", item, schema_def["items"], line=line)


def validate_schema(
    data: Dict[str, Any],
    schema: Dict[str, Dict[str, Any]],
    required_fields: Optional[List[str]] = None,
    strict: bool = False,
    path: Optional[str] = None,
    line: Optional[int] = None
) -> None:
    """
    Validate a dictionary against a schema definition.
    
    Args:
        data: The dictionary to validate
        schema: Schema definition mapping field names to their type definitions
        required_fields: List of field names that must be present
        strict: If True, reject fields not defined in schema
        path: Optional path string for error messages
        line: Optional line number for error messages
    
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError(
            f"Expected object, got {type(data).__name__}",
            path=path,
            line=line
        )
    
    # Check required fields
    if required_fields:
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing)}",
                path=path,
                line=line
            )
    
    # Validate each field
    for field_name, value in data.items():
        if field_name in schema:
            _validate_field(field_name, value, schema[field_name], line=line)
        elif strict:
            raise ValidationError(
                f"Unexpected field '{field_name}' not in schema",
                path=path,
                line=line
            )

def validate_jsonl_schema(
    file_path: Union[str, Path],
    schema: Dict[str, Dict[str, Any]],
    required_fields: Optional[List[str]] = None,
    strict: bool = False,
    max_lines: Optional[int] = None
) -> Dict[str, Any]:
    """
    Validate a JSONL file against a schema definition.
    
    Args:
        file_path: Path to the JSONL file
        schema: Schema definition for each line
        required_fields: List of required field names
        strict: If True, reject fields not in schema
        max_lines: Maximum number of lines to validate (for performance)
    
    Returns:
        Dictionary with validation statistics:
        {
            "total_lines": int,
            "valid_lines": int,
            "invalid_lines": int,
            "errors": List[Dict with line number and error message]
        }
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValidationError: If any line fails validation
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"JSONL file not found: {file_path}")
    
    stats = {
        "total_lines": 0,
        "valid_lines": 0,
        "invalid_lines": 0,
        "errors": []
    }
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            stats["total_lines"] += 1
            
            if max_lines and stats["total_lines"] > max_lines:
                break
            
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                validate_schema(data, schema, required_fields, strict, str(file_path), line_num)
                stats["valid_lines"] += 1
            except json.JSONDecodeError as e:
                stats["invalid_lines"] += 1
                stats["errors"].append({
                    "line": line_num,
                    "error": f"JSON decode error: {str(e)}"
                })
            except ValidationError as e:
                stats["invalid_lines"] += 1
                stats["errors"].append({
                    "line": line_num,
                    "error": str(e)
                })
    
    return stats

# Common schema definitions for llmXive pipeline

SYNTHETIC_FRAME_SCHEMA = {
    "frame_id": {"type": "string", "min_length": 1},
    "timestamp": {"type": "number", "minimum": 0},
    "video_id": {"type": "string", "min_length": 1},
    "width": {"type": "integer", "minimum": 1},
    "height": {"type": "integer", "minimum": 1},
    "label": {"type": "string", "enum": ["critical", "silence", "ambiguous"]},
    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0}
}

INTERNAL_STATE_SCHEMA = {
    "frame_id": {"type": "string", "min_length": 1},
    "timestamp": {"type": "number", "minimum": 0},
    "hidden_state_dim": {"type": "integer", "minimum": 1},
    "attention_shape": {"type": "array", "items": {"type": "integer"}},
    "features": {"type": "array", "items": {"type": "number"}}
}

SCHEDULER_DECISION_SCHEMA = {
    "decision_id": {"type": "string", "min_length": 1},
    "timestamp": {"type": "number", "minimum": 0},
    "intervention": {"type": "boolean"},
    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    "reason": {"type": "string", "max_length": 500}
}

MANIFEST_ENTRY_SCHEMA = {
    "video_id": {"type": "string", "min_length": 1},
    "duration_seconds": {"type": "number", "minimum": 0},
    "frame_count": {"type": "integer", "minimum": 1},
    "source": {"type": "string", "min_length": 1},
    "created_at": {"type": "string", "min_length": 1}
}
