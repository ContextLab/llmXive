"""
Contract validator utilities.

This module loads JSON‑Schema definitions from the project's
``specs/001-build-a-mesh-network-that-forms-the-larg/contracts`` directory
and validates arbitrary data against them.

It now accepts either a short schema name (e.g. ``"physical-node"``) or the
full filename (e.g. ``"physical-node.schema.yaml"``) – the latter is what the
contract‑test suite passes.  When an unknown schema name is requested a
``ValueError`` is raised, satisfying the unit‑test expectation.
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
    # Allow callers to pass the full filename; strip the extension if present
    if schema_name.endswith(".schema.yaml"):
        schema_name = schema_name.replace(".schema.yaml", "")
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
        # The test suite expects a ``ValueError`` for unknown schemas.
        raise ValueError(f"Schema file not found for {schema_name}: {path}")

    schema = load_schema_from_yaml(path)
    _SCHEMA_CACHE[schema_name] = schema
    return schema

def validate_schema(data: Dict[str, Any], schema_name: str) -> bool:
    """
    Validate ``data`` against the JSON‑Schema identified by ``schema_name``.

    ``schema_name`` may be a short name (``"physical-node"``) or the full
    filename (``"physical-node.schema.yaml"``).  Returns ``True`` if validation
    succeeds; otherwise raises a ``jsonschema.exceptions.ValidationError``.
    """
    import jsonschema

    # Normalise the name so that both forms work.
    if schema_name.endswith(".schema.yaml"):
        schema_name = schema_name.replace(".schema.yaml", "")

    schema = _load_schema(schema_name)
    jsonschema.validate(instance=data, schema=schema)
    log.debug("Data validated against schema '%s'", schema_name)
    return True
