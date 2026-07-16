"""
Utility functions for contract validation, schema loading, and file I/O.

This module provides helpers to:
- Load JSON and CSV schemas from disk
- Validate data against JSON schemas
- Load and save JSON/CSV files with type safety
- Validate specific output contracts (e.g., drift_result schema)
- Validate UUID formats
"""
import json
import csv
import os
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, TextIO

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None

# Import jsonschema dynamically to avoid hard dependency if not installed
# but we assume it's in requirements.txt per T002
try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    jsonschema = None


def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON or YAML schema from disk.
    
    Args:
        schema_path: Path to the schema file (.json or .yaml/.yml)
        
    Returns:
        Dictionary containing the parsed schema
        
    Raises:
        FileNotFoundError: If the schema file does not exist
        ValueError: If the file extension is not supported
        json.JSONDecodeError: If the JSON is invalid
        yaml.YAMLError: If the YAML is invalid (when using YAML)
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
        
    suffix = path.suffix.lower()
    
    with open(path, 'r', encoding='utf-8') as f:
        if suffix in ['.yaml', '.yml']:
            if not YAML_AVAILABLE:
                raise ImportError("PyYAML is required to load YAML schemas. Install with: pip install pyyaml")
            return yaml.safe_load(f)
        elif suffix == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Unsupported schema format: {suffix}. Use .json, .yaml, or .yml")


def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate a data dictionary against a JSON schema.
    
    Args:
        data: The data to validate
        schema: The JSON schema to validate against
        
    Returns:
        True if valid
        
    Raises:
        jsonschema.ValidationError: If validation fails
        ImportError: If jsonschema library is not installed
    """
    if not JSONSCHEMA_AVAILABLE:
        raise ImportError("jsonschema is required for validation. Install with: pip install jsonschema")
    
    jsonschema.validate(instance=data, schema=schema)
    return True


def load_json_file(file_path: Union[str, Path]) -> Any:
    """
    Load and parse a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON content (dict, list, etc.)
        
    Raises:
        FileNotFoundError: If file does not exist
        json.JSONDecodeError: If JSON is invalid
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
        
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data: Any, file_path: Union[str, Path], indent: int = 2) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data: Data to serialize to JSON
        file_path: Destination path
        indent: Indentation level for pretty-printing
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def load_csv_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> List[Dict[str, str]]:
    """
    Load a CSV file into a list of dictionaries.
    
    Args:
        file_path: Path to the CSV file
        encoding: Character encoding (default: utf-8)
        
    Returns:
        List of dictionaries, one per row
        
    Raises:
        FileNotFoundError: If file does not exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
        
    with open(path, 'r', encoding=encoding, newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_csv_file(
    data: List[Dict[str, Any]], 
    file_path: Union[str, Path], 
    fieldnames: Optional[List[str]] = None,
    encoding: str = 'utf-8'
) -> None:
    """
    Save a list of dictionaries to a CSV file.
    
    Args:
        data: List of row dictionaries
        file_path: Destination path
        fieldnames: Optional list of column names. If None, inferred from first row.
        encoding: Character encoding (default: utf-8)
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if not data:
        # Write empty file if no data
        with open(path, 'w', encoding=encoding, newline='') as f:
            pass
        return

    if fieldnames is None:
        fieldnames = list(data[0].keys())
        
    with open(path, 'w', encoding=encoding, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def validate_drift_result_schema(result: Dict[str, Any]) -> bool:
    """
    Validate a drift scoring result against the standard drift_result schema.
    
    Expected fields based on task T017 and T010:
    - log_id (string, UUID format)
    - drift_score (float, 0.0 to 1.0)
    - review_flag (boolean or string 'true'/'false')
    
    Args:
        result: The drift result dictionary to validate
        
    Returns:
        True if valid
        
    Raises:
        jsonschema.ValidationError: If validation fails
    """
    schema = {
        "type": "object",
        "properties": {
            "log_id": {
                "type": "string",
                "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
            },
            "drift_score": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0
            },
            "review_flag": {
                "oneOf": [
                    {"type": "boolean"},
                    {"type": "string", "enum": ["true", "false", "True", "False"]}
                ]
            }
        },
        "required": ["log_id", "drift_score", "review_flag"],
        "additionalProperties": True
    }
    
    if not JSONSCHEMA_AVAILABLE:
        # Fallback to manual validation if jsonschema not available
        if not isinstance(result.get("log_id"), str):
            raise ValueError("log_id must be a string")
        if not is_valid_uuid4(result.get("log_id", "")):
            raise ValueError("log_id must be a valid UUID4")
        
        score = result.get("drift_score")
        if not isinstance(score, (int, float)) or score < 0.0 or score > 1.0:
            raise ValueError("drift_score must be a number between 0.0 and 1.0")
        
        flag = result.get("review_flag")
        if not isinstance(flag, (bool, str)):
            raise ValueError("review_flag must be boolean or string")
        if isinstance(flag, str) and flag.lower() not in ["true", "false"]:
            raise ValueError("review_flag string must be 'true' or 'false'")
        
        return True
        
    return validate_against_schema(result, schema)


def is_valid_uuid4(uuid_string: str) -> bool:
    """
    Check if a string is a valid UUID4.
    
    Args:
        uuid_string: String to validate
        
    Returns:
        True if valid UUID4, False otherwise
    """
    if not isinstance(uuid_string, str):
        return False
    try:
        val = uuid.UUID(uuid_string, version=4)
        return str(val) == uuid_string
    except (ValueError, AttributeError):
        return False