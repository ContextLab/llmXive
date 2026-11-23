import json
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, Optional, List
from datetime import datetime

def compute_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a JSON schema from file."""
    with open(schema_path, 'r') as f:
        return json.load(f)

def validate_against_schema(data: Any, schema: Dict[str, Any]) -> bool:
    """Simple validation against a schema (placeholder for full jsonschema library)."""
    # In a real implementation, use jsonschema.validate(data, schema)
    # For now, we just check basic existence if schema defines required keys
    if "required" in schema:
        if isinstance(data, dict):
            for key in schema["required"]:
                if key not in data:
                    return False
    return True

def update_checksums(checksums_path: str, new_file_path: str):
    """Update the checksums registry with a new file."""
    registry = {"files": {}, "last_updated": datetime.now().isoformat(), "version": "1.0.0"}

    if os.path.exists(checksums_path):
        try:
            with open(checksums_path, 'r') as f:
                registry = json.load(f)
        except json.JSONDecodeError:
            registry = {"files": {}, "last_updated": datetime.now().isoformat(), "version": "1.0.0"}

    checksum = compute_checksum(new_file_path)
    registry["files"][new_file_path] = {
        "checksum": checksum,
        "updated_at": datetime.now().isoformat()
    }

    with open(checksums_path, 'w') as f:
        json.dump(registry, f, indent=2)

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """Verify the checksum of a file against an expected value."""
    actual = compute_checksum(file_path)
    return actual == expected_checksum

def verify_registry_entry(checksums_path: str, file_path: str) -> bool:
    """Verify a file exists in the registry and its checksum matches."""
    if not os.path.exists(checksums_path):
        return False

    with open(checksums_path, 'r') as f:
        registry = json.load(f)

    if file_path not in registry["files"]:
        return False

    expected = registry["files"][file_path]["checksum"]
    return verify_checksum(file_path, expected)
