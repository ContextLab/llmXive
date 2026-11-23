"""
Contract tests for the three schema definitions used in the project.

The tests verify that the schema files can be loaded and that the
validation helper (`validate_schema`) behaves as expected for a
minimal valid example.  The schemas are expected to be located in the
repository's ``contracts`` directory.
"""

import pathlib
import pytest

from orchestrator.contract_validator import load_schema_from_yaml, validate_schema

# Resolve the contracts directory relative to the project root.
CONTRACTS_DIR = pathlib.Path(__file__).parents[3] / "contracts"

# Expected schema filenames (must exist in the repository).
SCHEMA_FILES = {
    "physical_node": "physical_node.yaml",
    "execution_run": "execution_run.yaml",
    "regression_model": "regression_model.yaml",
}

def _load_schema(name: str):
    schema_path = CONTRACTS_DIR / SCHEMA_FILES[name]
    assert schema_path.is_file(), f"Schema file {schema_path} not found"
    return load_schema_from_yaml(schema_path)

@pytest.mark.parametrize("schema_name", list(SCHEMA_FILES.keys()))
def test_schema_loads(schema_name):
    """Each contract schema must be loadable as a valid YAML dict."""
    schema = _load_schema(schema_name)
    assert isinstance(schema, dict)
    # Basic sanity: a schema should contain a ``type`` key at top level.
    assert "type" in schema

def test_validate_schema_accepts_minimal_valid_data():
    """
    Verify that ``validate_schema`` returns ``True`` for a minimal
    document that satisfies the physical_node schema.
    """
    schema = _load_schema("physical_node")
    # Construct a minimal valid instance based on typical fields.
    valid_instance = {
        "id": "node-001",
        "hostname": "mock-node-001",
        "ip_address": "192.168.1.101",
        "status": "online",
        "available_memory_mb": 4096,
        "cpu_cores": 4,
    }
    assert validate_schema(valid_instance, "physical_node") is True

def test_validate_schema_rejects_invalid_data():
    """
    ``validate_schema`` should raise ``ValueError`` when required fields
    are missing.
    """
    schema = _load_schema("execution_run")
    invalid_instance = {
        "id": "run-001",
        # Missing required fields like ``node_count`` and ``granularity``
    }
    with pytest.raises(ValueError):
        validate_schema(invalid_instance, "execution_run")