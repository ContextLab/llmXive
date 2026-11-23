"""
Simple JSON‑Schema validator used by the contract‑test suite.

The original repository referenced a more elaborate validator, but
for the current verification we implement a minimal, dependency‑free
version that loads YAML schemas from the ``contracts`` directory
and validates JSON data with ``jsonschema``.
"""

import json
import yaml
from pathlib import Path
from jsonschema import validate, ValidationError

def load_schema_from_yaml(yaml_path: Path) -> dict:
    """
    Load a JSON‑Schema definition from a YAML file.

    Parameters
    ----------
    yaml_path: Path
        Path to the ``*.schema.yaml`` file.

    Returns
    -------
    dict
        The parsed schema.
    """
    if not yaml_path.is_file():
        raise FileNotFoundError(f"Schema file not found: {yaml_path}")
    with yaml_path.open("rt", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_schema(data: dict, schema_name: str) -> bool:
    """
    Validate *data* against the schema identified by *schema_name*.

    ``schema_name`` is expected to be the filename of a schema located
    in the top‑level ``contracts`` directory (e.g.
    ``physical-node.schema.yaml``).  The function loads the schema,
    validates the JSON data and returns ``True`` if validation succeeds.
    If validation fails a ``ValueError`` is raised – this matches the
    behaviour expected by the existing test suite.
    """
    schema_path = Path("contracts") / schema_name
    schema = load_schema_from_yaml(schema_path)
    try:
        validate(instance=data, schema=schema)
    except ValidationError as exc:
        raise ValueError(f"Schema validation failed for {schema_name}: {exc}") from exc
    return True
