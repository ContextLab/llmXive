import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

class SchemaValidationError(Exception):
    """Exception raised when schema validation fails."""
    pass

def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """Load a JSON schema from a file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def validate_iso_datetime(date_string: str) -> bool:
    """Validate an ISO 8601 datetime string."""
    try:
        datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False

def validate_sha256_checksum(checksum: str) -> bool:
    """Validate a SHA-256 checksum string (64 hex characters)."""
    if not isinstance(checksum, str):
        return False
    return bool(re.match(r'^[a-f0-9]{64}$', checksum.lower()))

def validate_path_pattern(path: Union[str, Path]) -> bool:
    """Validate that a path string follows expected patterns."""
    path_str = str(path)
    # Basic validation: no null bytes, not absolute if relative expected
    if '\x00' in path_str:
        return False
    return True

def validate_artifact(artifact: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate an artifact dictionary against a schema."""
    # Simple validation: check required fields exist
    required = schema.get('required', [])
    for field in required:
        if field not in artifact:
            raise SchemaValidationError(f"Missing required field: {field}")
    return True

def validate_output_file(output_path: Union[str, Path], expected_extension: str) -> bool:
    """Validate that an output file path has the expected extension."""
    path = Path(output_path)
    if path.suffix != expected_extension:
        raise SchemaValidationError(f"Expected extension {expected_extension}, got {path.suffix}")
    return True
