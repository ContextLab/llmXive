"""
Unit tests for schema documentation and contract validity.

These tests ensure that the schema files in `contracts/` are valid YAML,
can be loaded by the validator, and match the descriptions in the documentation.
"""

import json
import os
import yaml
import pytest
from pathlib import Path

# Project root relative to this test file
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DOCS_DIR = PROJECT_ROOT / "specs" / "001-topology-thermal-conductivity"


def test_contracts_directory_exists():
    """Verify that the contracts directory exists."""
    assert CONTRACTS_DIR.exists(), f"Contracts directory not found at {CONTRACTS_DIR}"


def test_required_schemas_exist():
    """Verify that all required schema files exist."""
    required_schemas = [
        "atomic_graph.schema.yaml",
        "thermal_sample.schema.yaml",
        "gnn_output.schema.yaml"
    ]
    for schema_name in required_schemas:
        schema_path = CONTRACTS_DIR / schema_name
        assert schema_path.exists(), f"Schema file missing: {schema_path}"


def test_schemas_are_valid_yaml():
    """Verify that all schema files are valid YAML."""
    schema_files = list(CONTRACTS_DIR.glob("*.yaml"))
    assert len(schema_files) > 0, "No schema files found in contracts directory"

    for schema_file in schema_files:
        with open(schema_file, "r") as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {schema_file}: {e}")


def test_atomic_graph_schema_structure():
    """Verify the structure of atomic_graph.schema.yaml matches documentation."""
    schema_path = CONTRACTS_DIR / "atomic_graph.schema.yaml"
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)

    # Check top-level keys
    assert "type" in schema, "Schema must have 'type' field"
    assert schema["type"] == "object", "atomic_graph schema must be an object"

    # Check required fields
    required = schema.get("required", [])
    assert "graph_id" in required, "graph_id must be required"
    assert "nodes" in required, "nodes must be required"
    assert "edges" in required, "edges must be required"

    # Check properties
    props = schema.get("properties", {})
    assert "nodes" in props, "nodes property must exist"
    assert "edges" in props, "edges property must exist"

    # Check node structure
    node_items = props["nodes"].get("items", {}).get("properties", {})
    assert "id" in node_items, "Node must have 'id'"
    assert "coords" in node_items, "Node must have 'coords'"
    assert "degree" in node_items, "Node must have 'degree'"
    assert "clustering_coeff" in node_items, "Node must have 'clustering_coeff'"


def test_thermal_sample_schema_structure():
    """Verify the structure of thermal_sample.schema.yaml matches documentation."""
    schema_path = CONTRACTS_DIR / "thermal_sample.schema.yaml"
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)

    required = schema.get("required", [])
    assert "graph_id" in required
    assert "conductivity" in required
    assert "converged" in required
    assert "metadata" in required

    props = schema.get("properties", {})
    assert "conductivity" in props
    assert "converged" in props
    assert "metadata" in props


def test_gnn_output_schema_structure():
    """Verify the structure of gnn_output.schema.yaml matches documentation."""
    schema_path = CONTRACTS_DIR / "gnn_output.schema.yaml"
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)

    required = schema.get("required", [])
    assert "predicted_flux" in required
    assert "loss" in required
    assert "epoch" in required


def test_documentation_files_exist():
    """Verify that documentation files for schemas exist."""
    doc_files = [
        "002-data-models.md",
        "003-schema-overview.md",
        "004-data-flow.md"
    ]
    for doc_file in doc_files:
        doc_path = DOCS_DIR / doc_file
        assert doc_path.exists(), f"Documentation file missing: {doc_path}"


def test_documentation_references_schemas():
    """Verify that documentation references the correct schema files."""
    doc_path = DOCS_DIR / "002-data-models.md"
    with open(doc_path, "r") as f:
        content = f.read()

    # Check for references to schema files
    assert "atomic_graph.schema.yaml" in content
    assert "thermal_sample.schema.yaml" in content
    assert "gnn_output.schema.yaml" in content


def test_schema_validation_integration():
    """Integration test: Load a schema and validate it using the project's validator."""
    # This test ensures that the schemas can be loaded by the actual validator code
    from ingest.validators import load_schema

    schema_path = CONTRACTS_DIR / "atomic_graph.schema.yaml"
    try:
        schema = load_schema(schema_path)
        assert schema is not None, "Schema loading failed"
    except Exception as e:
        pytest.fail(f"Failed to load schema via project validator: {e}")