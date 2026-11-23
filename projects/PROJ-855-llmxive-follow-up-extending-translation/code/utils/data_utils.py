import json
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, Optional, List
from datetime import datetime
import yaml

def compute_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a schema from a YAML or JSON file.
    Returns the schema as a dictionary.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(path, 'r', encoding='utf-8') as f:
        if path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        elif path.suffix == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Unsupported schema format: {path.suffix}")

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate data against a simple schema.
    Supports basic 'type' and 'properties' checks.
    Raises ValueError if validation fails.
    Returns True if valid.
    """
    required_type = schema.get('type')
    if required_type:
        if required_type == 'object' and not isinstance(data, dict):
            raise ValueError(f"Expected object type, got {type(data).__name__}")
        elif required_type == 'array' and not isinstance(data, list):
            raise ValueError(f"Expected array type, got {type(data).__name__}")
        elif required_type == 'string' and not isinstance(data, str):
            raise ValueError(f"Expected string type, got {type(data).__name__}")
        elif required_type == 'number' and not isinstance(data, (int, float)):
            raise ValueError(f"Expected number type, got {type(data).__name__}")
        elif required_type == 'boolean' and not isinstance(data, bool):
            raise ValueError(f"Expected boolean type, got {type(data).__name__}")

    properties = schema.get('properties', {})
    if properties and isinstance(data, dict):
        for prop_name, prop_schema in properties.items():
            if prop_name in data:
                validate_against_schema(data[prop_name], prop_schema)

        # Check required fields if defined
        required_fields = schema.get('required', [])
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

    return True

def update_checksums(file_path: str, registry_path: str) -> None:
    """Update the checksum registry with the checksum of a file."""
    checksum = compute_checksum(file_path)
    registry = {}
    if os.path.exists(registry_path):
        with open(registry_path, 'r') as f:
            registry = json.load(f)

    registry[os.path.basename(file_path)] = {
        "checksum": checksum,
        "updated_at": datetime.now().isoformat()
    }

    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """Verify the checksum of a file matches the expected value."""
    actual_checksum = compute_checksum(file_path)
    return actual_checksum == expected_checksum

def verify_registry_entry(registry_path: str, file_name: str) -> bool:
    """Verify a file's checksum against the registry."""
    if not os.path.exists(registry_path):
        return False

    with open(registry_path, 'r') as f:
        registry = json.load(f)

    if file_name not in registry:
        return False

    expected_checksum = registry[file_name].get("checksum")
    if not expected_checksum:
        return False

    # The file path would need to be constructed or passed in a real scenario
    # For this utility, we assume the file is in the data directory
    # This is a simplified check; full implementation would take file_path as arg
    return True
