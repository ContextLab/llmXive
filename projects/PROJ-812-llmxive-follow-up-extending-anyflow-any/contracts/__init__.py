"""
contracts package
-----------------

This package contains the base JSON‑Schema definitions for the four core
contract types used throughout the project:

* annotation
* metric
* result
* sensitivity

Helper utilities are provided for loading a schema and validating a
contract instance against its schema using the ``jsonschema`` library.
"""

import json
from pathlib import Path
from typing import Any, Dict

import yaml
from jsonschema import Draft7Validator, ValidationError

__all__ = [
    "load_schema",
    "validate_contract",
]


def _schema_path(name: str) -> Path:
    """
    Return the absolute path to the JSON‑Schema file for ``name``.
    The convention is ``<name>_schema.json`` inside the ``contracts`` package.
    """
    return Path(__file__).with_name(f"{name}_schema.json")


def load_schema(name: str) -> Dict[str, Any]:
    """
    Load and return the JSON‑Schema dictionary for the given contract name.

    Parameters
    ----------
    name: str
        One of ``annotation``, ``metric``, ``result`` or ``sensitivity``.

    Returns
    -------
    dict
        The parsed JSON‑Schema.
    """
    schema_file = _schema_path(name)
    if not schema_file.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    with schema_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_contract(contract_path: Path, schema_name: str) -> None:
    """
    Validate a contract instance (YAML or JSON) against the named schema.

    Parameters
    ----------
    contract_path: pathlib.Path
        Path to the contract file. The function auto‑detects YAML (``.yaml``,
        ``.yml``) or JSON (``.json``) based on the suffix.
    schema_name: str
        Name of the schema to validate against (e.g. ``"annotation"``).

    Raises
    ------
    jsonschema.ValidationError
        If the contract does not conform to the schema.
    FileNotFoundError
        If either the contract file or the schema file cannot be found.
    """
    if not contract_path.is_file():
        raise FileNotFoundError(f"Contract file not found: {contract_path}")

    # Load contract data
    if contract_path.suffix.lower() in {".yaml", ".yml"}:
        with contract_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    elif contract_path.suffix.lower() == ".json":
        with contract_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        raise ValueError(
            f"Unsupported contract file type: {contract_path.suffix}"
        )

    schema = load_schema(schema_name)
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

    if errors:
        # Raise the first error with a helpful message
        first = errors[0]
        raise ValidationError(
            f"Contract validation failed for {contract_path} against schema "
            f"'{schema_name}': {first.message}"
        )
