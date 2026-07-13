"""
Utility functions for data handling: checksums, schema validation.
"""
import json
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, Optional, List
from datetime import datetime

def compute_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a JSON schema from file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found at {schema_path}")
    
    with open(schema_path, 'r') as f:
        return json.load(f)

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Basic validation of data against a schema.
    Checks for required keys and types.
    """
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    
    for key in required:
        if key not in data:
            return False
        
        if key in properties:
            expected_type = properties[key].get("type")
            actual_value = data[key]
            
            # Simple type checking
            type_map = {
                "string": str,
                "number": (int, float),
                "integer": int,
                "boolean": bool,
                "array": list,
                "object": dict
            }
            
            if expected_type in type_map:
                if not isinstance(actual_value, type_map[expected_type]):
                    return False
    
    return True

def update_checksums(checksums_path: Path, new_file: Path) -> None:
    """Update checksums.json with a new file's checksum."""
    if checksums_path.exists():
        with open(checksums_path, 'r') as f:
            checksums = json.load(f)
    else:
        checksums = {}
    
    checksums[new_file.name] = {
        "hash": compute_checksum(new_file),
        "timestamp": datetime.now().isoformat(),
        "path": str(new_file)
    }
    
    with open(checksums_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def verify_checksum(file_path: Path, expected_hash: str) -> bool:
    """Verify a file's checksum matches the expected hash."""
    actual_hash = compute_checksum(file_path)
    return actual_hash == expected_hash

def verify_registry_entry(checksums_path: Path, file_name: str) -> bool:
    """Verify a file exists and its checksum matches the registry."""
    if not checksums_path.exists():
        return False
    
    with open(checksums_path, 'r') as f:
        checksums = json.load(f)
    
    if file_name not in checksums:
        return False
    
    file_path = Path(checksums[file_name]["path"])
    if not file_path.exists():
        return False
    
    return verify_checksum(file_path, checksums[file_name]["hash"])
