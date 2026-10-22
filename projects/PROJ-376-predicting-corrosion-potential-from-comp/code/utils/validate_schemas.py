"""
Utility for validating a Python ``dict`` against a JSON‑Schema file.

The public function ``validate`` raises ``jsonschema.exceptions.ValidationError``
if the data does not conform to the supplied schema.
"""

import json
from pathlib import Path
from typing import Any, Mapping

import jsonschema

def _load_schema(schema_path: Path) -> Mapping[str, Any]:
    """
    Load a JSON‑Schema from a YAML or JSON file.

    Parameters
    ----------
    schema_path: Path
        Path to the schema file.

    Returns
    -------
    dict
        The parsed schema.
    """
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        # The schema files are written in YAML but are also valid JSON.
        # ``json.load`` can parse both because the files use JSON‑compatible syntax.
        return json.load(f)

def validate(data: dict, schema_path: Path) -> None:
    """
    Validate ``data`` against the JSON‑Schema located at ``schema_path``.

    Parameters
    ----------
    data: dict
        The data instance to validate.
    schema_path: Path
        Path to a JSON‑Schema file.

    Raises
    ------
    jsonschema.exceptions.ValidationError
        If ``data`` does not conform to the schema.
    FileNotFoundError
        If the schema file cannot be found.
    """
    schema = _load_schema(schema_path)
    jsonschema.validate(instance=data, schema=schema)
