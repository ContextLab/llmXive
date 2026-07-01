import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Optional dependency: jsonschema. If not installed, validation is skipped but logged.
try:
    import jsonschema
    from jsonschema import validate, ValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    validate = None  # type: ignore
    ValidationError = Exception  # type: ignore

SCHEMAS_DIR = Path(__file__).parent.parent.parent / "contracts"

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a YAML schema from the contracts directory."""
    schema_path = SCHEMAS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_record(record: Dict[str, Any], schema_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a single record (dict) against a named schema.
    
    Returns:
        Tuple of (is_valid, error_message).
        If jsonschema is not installed, it returns (True, "Validation skipped: jsonschema not installed").
    """
    if not HAS_JSONSCHEMA:
        return True, "Validation skipped: jsonschema not installed"

    try:
        schema = load_schema(schema_name)
        validate(instance=record, schema=schema)
        return True, None
    except ValidationError as e:
        return False, str(e.message)

def validate_dataset(data: List[Dict[str, Any]], schema_name: str) -> List[str]:
    """
    Validate a list of records against a schema.
    
    Returns:
        List of error messages for invalid records.
    """
    errors = []
    for i, record in enumerate(data):
        is_valid, error_msg = validate_record(record, schema_name)
        if not is_valid:
            errors.append(f"Record {i}: {error_msg}")
    return errors