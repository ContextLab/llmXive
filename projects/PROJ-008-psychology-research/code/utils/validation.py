"""
Schema‑validation utilities for the project.

This module provides two thin wrappers around ``jsonschema.validate`` that
load the JSON‑Schema contracts stored under ``contracts/`` and validate a
Python ``dict`` against them.

The functions raise ``jsonschema.exceptions.ValidationError`` if the data
does not conform to the schema; otherwise they simply return ``True``.
"""

import json
from pathlib import Path
from typing import Any, Dict

import yaml
from jsonschema import Draft7Validator, ValidationError

# Resolve the project‑root ``contracts`` directory once.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]  # <project>/code/utils/validation.py → <project>
_CONTRACTS_DIR = _PROJECT_ROOT / "contracts"


def _load_schema(schema_filename: str) -> Dict[str, Any]:
    """
    Load a YAML JSON‑Schema file from the ``contracts`` directory.

    Parameters
    ----------
    schema_filename: str
        The filename of the schema (e.g. ``cleaned_study.schema.yaml``).

    Returns
    -------
    dict
        The parsed JSON‑Schema.
    """
    schema_path = _CONTRACTS_DIR / schema_filename
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with schema_path.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    if not isinstance(schema, dict):
        raise ValueError(f"Schema file {schema_path} does not contain a valid mapping.")
    return schema


def _validate(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Core validation logic using ``jsonschema.Draft7Validator``.

    Returns ``True`` when the data is valid; otherwise raises
    ``jsonschema.exceptions.ValidationError``.
    """
    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(data))
    if errors:
        # Raise the first error for simplicity – pytest can catch it.
        raise errors[0]
    return True


def validate_cleaned_study(data: Dict[str, Any]) -> bool:
    """
    Validate a cleaned‑study record against the
    ``cleaned_study.schema.yaml`` contract.

    Parameters
    ----------
    data: dict
        The cleaned study record to validate.

    Returns
    -------
    bool
        ``True`` if validation succeeds.

    Raises
    ------
    jsonschema.exceptions.ValidationError
        If the record does not conform to the schema.
    FileNotFoundError
        If the schema file cannot be located.
    """
    schema = _load_schema("cleaned_study.schema.yaml")
    return _validate(data, schema)


def validate_effect_size(data: Dict[str, Any]) -> bool:
    """
    Validate an effect‑size record against the
    ``effect_size.schema.yaml`` contract.

    Parameters
    ----------
    data: dict
        The effect‑size record to validate.

    Returns
    -------
    bool
        ``True`` if validation succeeds.

    Raises
    ------
    jsonschema.exceptions.ValidationError
        If the record does not conform to the schema.
    FileNotFoundError
        If the schema file cannot be located.
    """
    schema = _load_schema("effect_size.schema.yaml")
    return _validate(data, schema)


__all__ = [
    "validate_cleaned_study",
    "validate_effect_size",
]
