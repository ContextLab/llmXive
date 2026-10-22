"""
Unit tests for ``code.utils.validate_schemas.validate``.

The tests load the two contract schemas that ship with the project
(``ingest.schema.yaml`` and ``dataset.schema.yaml``) and construct a
minimal, but schema‑conforming, instance for each.  The construction logic
is generic – it inspects the ``required`` properties of the top‑level
object and creates placeholder values based on the declared ``type``.
This approach guarantees that the test does not need to know the exact
field names or types a priori, making it robust to future schema changes.
"""

import json
from pathlib import Path
from typing import Any, Mapping

import yaml

from code.utils.validate_schemas import validate

# ----------------------------------------------------------------------
# Helper: generate a dummy instance that satisfies a given JSON‑Schema.
# ----------------------------------------------------------------------
def _dummy_for_type(subschema: Mapping[str, Any]) -> Any:
    """Return a placeholder value that matches ``subschema``."""
    schema_type = subschema.get("type")

    # ``type`` may be a list – pick the first entry.
    if isinstance(schema_type, list):
        schema_type = schema_type[0]

    # Respect ``enum`` and ``const`` if present.
    if "const" in subschema:
        return subschema["const"]
    if "enum" in subschema and isinstance(subschema["enum"], list):
        return subschema["enum"][0]

    if schema_type == "string":
        # Use a generic ISO‑8601 timestamp for date‑time strings.
        fmt = subschema.get("format")
        if fmt in {"date-time", "date"}:
            return "2020-01-01T00:00:00Z"
        return "example"
    if schema_type == "integer":
        return 0
    if schema_type == "number":
        return 0.0
    if schema_type == "boolean":
        return True
    if schema_type == "array":
        # Empty list satisfies most array constraints.
        return []
    if schema_type == "object":
        return _generate_dummy(subschema)
    # Fallback – ``null`` or unknown types.
    return None

def _generate_dummy(schema: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Recursively generate a minimal instance that satisfies ``schema``.
    Only required properties are populated.
    """
    if not isinstance(schema, dict):
        raise TypeError("Schema must be a mapping")

    if schema.get("type") != "object":
        # For non‑object top‑level schemas we simply return a dummy.
        return {"value": _dummy_for_type(schema)}  # type: ignore[return-value]

    properties = schema.get("properties", {})
    required = schema.get("required", [])

    instance: dict[str, Any] = {}
    for prop in required:
        prop_schema = properties.get(prop, {})
        instance[prop] = _dummy_for_type(prop_schema)

    return instance

# ----------------------------------------------------------------------
# Test fixtures – locate the contract schemas relative to this file.
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]

INGEST_SCHEMA = (
    PROJECT_ROOT
    / "specs"
    / "001-predict-corrosion-potential-from-comp"
    / "contracts"
    / "ingest.schema.yaml"
)
DATASET_SCHEMA = (
    PROJECT_ROOT
    / "specs"
    / "001-predict-corrosion-potential-from-comp"
    / "contracts"
    / "dataset.schema.yaml"
)

# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------
def test_validate_ingest_schema():
    """Validate a dummy record against the ingest schema."""
    dummy = _generate_dummy(yaml.safe_load(INGEST_SCHEMA.read_text()))
    # ``validate`` should raise no exception for a conforming instance.
    validate(dummy, INGEST_SCHEMA)

def test_validate_dataset_schema():
    """Validate a dummy record against the processed dataset schema."""
    dummy = _generate_dummy(yaml.safe_load(DATASET_SCHEMA.read_text()))
    validate(dummy, DATASET_SCHEMA)