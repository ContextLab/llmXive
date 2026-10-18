"""
Schema validator for session data using a relaxed JSON schema.

This module provides a single function `validate_session` that validates a
Python dictionary representing a session against the relaxed schema
located at:
`specs/001-improving-accessibility-and-usability-of/contracts/session_relaxed.schema.yaml`.

It returns ``True`` if the data conforms to the schema and ``False`` otherwise.
Any issues loading the schema itself raise ``FileNotFoundError``.
"""

import jsonschema
from pathlib import Path
from typing import Any, Dict

# Resolve the path to the relaxed session schema.
# The file hierarchy is:
# <project_root>/specs/001-improving-accessibility-and-usability-of/contracts/session_relaxed.schema.yaml
SCHEMA_PATH = (
    Path(__file__).parents[3]
    / "specs"
    / "001-improving-accessibility-and-usability-of"
    / "contracts"
    / "session_relaxed.schema.yaml"
)

def _load_schema() -> Dict[str, Any]:
    """Load the relaxed JSON schema from disk.

    Returns:
        The schema as a Python dictionary.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError / json.JSONDecodeError: If the file cannot be parsed.
    """
    if not SCHEMA_PATH.is_file():
        raise FileNotFoundError(f"Relaxed session schema not found at {SCHEMA_PATH}")

    # The schema is a YAML file; use PyYAML (already a project dependency).
    import yaml

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# Load once at import time – the schema is static for the lifetime of the process.
_RELAXED_SCHEMA = _load_schema()


def validate_session(data: Dict[str, Any]) -> bool:
    """
    Validate a session dictionary against the relaxed schema.

    Args:
        data: The session data to validate.

    Returns:
        True if ``data`` conforms to the schema, False otherwise.
    """
    try:
        jsonschema.validate(instance=data, schema=_RELAXED_SCHEMA)
        return True
    except jsonschema.ValidationError:
        return False
    except jsonschema.SchemaError as e:
        # A malformed schema is a developer error; raise loudly.
        raise RuntimeError(f"Invalid JSON schema loaded from {SCHEMA_PATH}: {e}") from e
