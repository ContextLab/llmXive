"""
Utility for validating a Python ``dict`` against a JSON‑Schema YAML file.

The function ``validate`` loads the YAML schema, then uses ``jsonschema``
to validate the supplied data.  If the data does not conform a
``jsonschema.ValidationError`` (or any subclass) is raised – callers can
catch this to turn validation failures into domain‑specific exceptions
such as ``SchemaMismatchError``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import yaml
from jsonschema import Draft7Validator, ValidationError, validate as _validate

__all__ = ["validate"]


def _load_schema(schema_path: Path) -> Mapping[str, Any]:
    """
    Load a JSON‑Schema definition from a YAML file.

    Parameters
    ----------
    schema_path: Path
        Path to the ``*.schema.yaml`` file.

    Returns
    -------
    Mapping[str, Any]
        The parsed schema.
    """
    if not isinstance(schema_path, Path):
        schema_path = Path(schema_path)

    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with schema_path.open("r", encoding="utf-8") as f:
        # ``yaml.safe_load`` returns ``dict``/``list`` structures that are
        # directly compatible with ``jsonschema``.
        schema = yaml.safe_load(f)

    if not isinstance(schema, dict):
        raise ValueError(f"Schema at {schema_path} is not a mapping")
    return schema


def validate(data: dict, schema_path: Path) -> None:
    """
    Validate ``data`` against the JSON‑Schema located at ``schema_path``.

    The function raises ``jsonschema.ValidationError`` (or a subclass) if
    ``data`` does not satisfy the schema.  Successful validation returns
    ``None``.

    Parameters
    ----------
    data: dict
        The JSON‑compatible data to validate.
    schema_path: Path
        Path to the YAML schema file.

    Raises
    ------
    jsonschema.ValidationError
        If ``data`` does not conform to the schema.
    FileNotFoundError
        If the schema file cannot be located.
    ValueError
        If the schema file does not contain a mapping.
    """
    if not isinstance(data, dict):
        raise TypeError("`data` must be a dictionary")

    schema = _load_schema(schema_path)

    # ``jsonschema.validate`` is a thin wrapper around ``Draft7Validator``.
    # Using the validator directly gives better error messages.
    validator = Draft7Validator(schema)
    validator.validate(data)