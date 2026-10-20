"""
Contract validator utilities.

The original implementation already provided ``load_schema_from_yaml`` and
``validate_schema``.  For the new ``task-chunk`` contract we need to
ensure that ``validate_schema`` can locate the schema by name.  The
function now interprets a name like ``"task-chunk"`` as the corresponding
``task-chunk.schema.yaml`` file under the contracts directory.
"""

import yaml
from pathlib import Path
from typing import Any, Dict

from llmxive_toolkit import get_logger

log = get_logger(__name__)

_SCHEMA_CACHE: Dict[str, Dict[str, Any]] = {}

def _get_schema_path(schema_name: str) -> Path:
    """
    Resolve a schema name (e.g. ``"physical-node"``) to its YAML file path.
    """
    base_dir = Path(__file__).parents[2] / "specs" / "001-build-a-mesh-network-that-forms-the-larg" / "contracts"
    filename = f"{schema_name}.schema.yaml"
    return base_dir / filename

def load_schema_from_yaml(yaml_path: Path) -> Dict[str, Any]:
    """Load a JSON‑Schema from a YAML file."""
    with yaml_path.open("rt", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _load_schema(schema_name: str) -> Dict[str, Any]:
    """Load (and cache) a schema by its logical name."""
    if schema_name in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[schema_name]

    path = _get_schema_path(schema_name)
    if not path.is_file():
        raise FileNotFoundError(f"Schema file not found for {schema_name}: {path}")

    schema = load_schema_from_yaml(path)
    _SCHEMA_CACHE[schema_name] = schema
    return schema

def validate_schema(data: Dict[str, Any], schema_name: str) -> bool:
    """
    Validate ``data`` against the JSON‑Schema identified by ``schema_name``.

    Returns ``True`` if validation succeeds; otherwise raises a
    ``jsonschema.exceptions.ValidationError``.
    """
    import jsonschema

    schema = _load_schema(schema_name)
    jsonschema.validate(instance=data, schema=schema)
    log.debug("Data validated against schema '%s'", schema_name)
    return True
