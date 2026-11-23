"""
Utility for validating Python ``dict`` objects against JSON‑Schema files.

The public function ``validate`` raises ``jsonschema.exceptions.ValidationError``
if the supplied data does not conform to the schema located at ``schema_path``.
"""
import json
from pathlib import Path
from typing import Any, Mapping

import yaml
from jsonschema import Draft7Validator, ValidationError

def _load_schema(schema_path: Path) -> Mapping[str, Any]:
    """
    Load a JSON‑Schema from a YAML or JSON file.

    Parameters
    ----------
    schema_path: Path
        Path to the schema file.

    Returns
    -------
    Mapping[str, Any]
        The parsed schema.
    """
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with schema_path.open("r", encoding="utf-8") as f:
        if schema_path.suffix in {".yaml", ".yml"}:
            return yaml.safe_load(f)
        else:
            return json.load(f)

def validate(data: dict, schema_path: Path) -> None:
    """
    Validate ``data`` against the JSON‑Schema located at ``schema_path``.

    Parameters
    ----------
    data: dict
        The data to validate.
    schema_path: Path
        Path to a JSON‑Schema file (YAML or JSON).

    Raises
    ------
    jsonschema.exceptions.ValidationError
        If ``data`` does not conform to the schema.
    """
    schema = _load_schema(schema_path)
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        # Raise the first error for simplicity; the test suite expects an exception.
        raise ValidationError(errors[0].message)
