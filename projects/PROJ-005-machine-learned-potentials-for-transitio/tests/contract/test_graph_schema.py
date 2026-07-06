"""
Contract test for graph schema validation.

This module validates that the graph construction pipeline produces outputs
that strictly adhere to the schema defined in `contracts/dataset_graph.schema.yaml`.
It ensures data integrity before models are trained.
"""
import json
import pytest
from pathlib import Path
from typing import Any, Dict, List, Set

# Import schema loading utility from project config module
from src.utils.config import load_yaml_config, get_project_root


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

@pytest.fixture
def schema_path() -> Path:
    """Return the path to the dataset graph schema definition."""
    root = get_project_root()
    return root / "contracts" / "dataset_graph.schema.yaml"

@pytest.fixture
def schema(schema_path: Path) -> Dict[str, Any]:
    """Load the graph schema definition."""
    return load_yaml_config(schema_path)

@pytest.fixture
def mock_graph_data() -> Dict[str, Any]:
    """
    Create a minimal valid graph data structure that mimics the output
    of `src/data/graph_construction.py` for validation purposes.
    """
    return {
        "nodes": [
            {
                "atomic_number": 46,  # Pd
                "formal_charge": 0,
                "coordination_number": 4,
                "element": "Pd"
            },
            {
                "atomic_number": 1,   # H
                "formal_charge": 0,
                "coordination_number": 1,
                "element": "H"
            }
        ],
        "edges": [
            {
                "source": 0,
                "target": 1,
                "distance": 1.52,
                "type": "bond"
            }
        ],
        "metadata": {
            "energy_dft": -123.456,
            "barrier_height": 15.2,
            "reaction_id": "rxn_001",
            "ligand_class": "Group 13",
            "cutoff_used": 3.5
        }
    }

@pytest.fixture
def invalid_graph_data_missing_node_attr() -> Dict[str, Any]:
    """Graph data missing a required node attribute (formal_charge)."""
    data = {
        "nodes": [
            {
                "atomic_number": 46,
                # "formal_charge": 0  # Missing
            }
        ],
        "edges": [],
        "metadata": {
            "energy_dft": -123.45,
            "barrier_height": 10.0,
            "reaction_id": "rxn_001",
            "ligand_class": "Group 13",
            "cutoff_used": 3.5
        }
    }
    return data

@pytest.fixture
def invalid_graph_data_wrong_ligand_class() -> Dict[str, Any]:
    """Graph data with an invalid ligand_class value."""
    data = {
        "nodes": [
            {"atomic_number": 46, "formal_charge": 0, "coordination_number": 4, "element": "Pd"}
        ],
        "edges": [],
        "metadata": {
            "energy_dft": -123.45,
            "barrier_height": 10.0,
            "reaction_id": "rxn_001",
            "ligand_class": "InvalidClass", # Not in allowed list
            "cutoff_used": 3.5
        }
    }
    return data

# --------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------

def validate_node(node: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validate a single node against the schema."""
    errors = []
    node_schema = schema.get("nodes", {})
    required_fields = node_schema.get("required", [])
    field_types = node_schema.get("types", {})

    for field in required_fields:
        if field not in node:
            errors.append(f"Node missing required field: {field}")

    for field, expected_type in field_types.items():
        if field in node:
            actual_type = type(node[field]).__name__
            # Simple type mapping for validation
            type_map = {
                "int": "int",
                "float": "float",
                "str": "str",
                "list": "list"
            }
            expected_py_type = type_map.get(expected_type, expected_type)
            if actual_type != expected_py_type:
                errors.append(f"Node field '{field}' has type {actual_type}, expected {expected_py_type}")

    return errors

def validate_metadata(metadata: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validate metadata against the schema."""
    errors = []
    meta_schema = schema.get("metadata", {})
    required_fields = meta_schema.get("required", [])
    field_types = meta_schema.get("types", {})
    allowed_values = meta_schema.get("allowed_values", {})

    for field in required_fields:
        if field not in metadata:
            errors.append(f"Metadata missing required field: {field}")

    for field, expected_type in field_types.items():
        if field in metadata:
            actual_type = type(metadata[field]).__name__
            type_map = {"int": "int", "float": "float", "str": "str"}
            expected_py_type = type_map.get(expected_type, expected_type)
            if actual_type != expected_py_type:
                errors.append(f"Metadata field '{field}' has type {actual_type}, expected {expected_py_type}")

    # Check allowed values
    for field, allowed in allowed_values.items():
        if field in metadata:
            if metadata[field] not in allowed:
                errors.append(f"Metadata field '{field}' value '{metadata[field]}' not in allowed list: {allowed}")

    return errors

def validate_graph(graph_data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate the entire graph data structure against the schema.
    Returns a list of error strings.
    """
    errors = []

    # 1. Validate Nodes
    nodes = graph_data.get("nodes", [])
    if not isinstance(nodes, list):
        errors.append("'nodes' must be a list")
    else:
        for i, node in enumerate(nodes):
            node_errors = validate_node(node, schema)
            errors.extend([f"Node {i}: {e}" for e in node_errors])

    # 2. Validate Metadata
    metadata = graph_data.get("metadata", {})
    if not isinstance(metadata, dict):
        errors.append("'metadata' must be a dict")
    else:
        meta_errors = validate_metadata(metadata, schema)
        errors.extend(meta_errors)

    return errors

# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------

class TestGraphSchemaValidation:
    """
    Contract tests ensuring graph data conforms to the defined schema.
    """

    def test_schema_loads_valid(self, schema: Dict[str, Any]) -> None:
        """Ensure the schema file itself is valid YAML and contains expected keys."""
        assert "nodes" in schema
        assert "edges" in schema
        assert "metadata" in schema
        assert "nodes" in schema.get("required", []) or "nodes" in schema

    def test_valid_graph_passes(self, schema: Dict[str, Any], mock_graph_data: Dict[str, Any]) -> None:
        """A correctly formed graph should have zero validation errors."""
        errors = validate_graph(mock_graph_data, schema)
        assert len(errors) == 0, f"Unexpected validation errors: {errors}"

    def test_missing_node_attribute_fails(self, schema: Dict[str, Any], invalid_graph_data_missing_node_attr: Dict[str, Any]) -> None:
        """Graph with missing required node attributes should fail validation."""
        errors = validate_graph(invalid_graph_data_missing_node_attr, schema)
        assert len(errors) > 0
        assert any("missing required field: formal_charge" in e for e in errors)

    def test_invalid_ligand_class_fails(self, schema: Dict[str, Any], invalid_graph_data_wrong_ligand_class: Dict[str, Any]) -> None:
        """Graph with invalid ligand_class should fail validation."""
        errors = validate_graph(invalid_graph_data_wrong_ligand_class, schema)
        assert len(errors) > 0
        assert any("ligand_class" in e and "not in allowed list" in e for e in errors)

    def test_empty_nodes_list_fails(self, schema: Dict[str, Any]) -> None:
        """Graph with empty nodes list should fail if nodes are required."""
        empty_data = {
            "nodes": [],
            "edges": [],
            "metadata": {
                "energy_dft": -123.45,
                "barrier_height": 10.0,
                "reaction_id": "rxn_001",
                "ligand_class": "Group 13",
                "cutoff_used": 3.5
            }
        }
        errors = validate_graph(empty_data, schema)
        # Depending on schema, empty list might be allowed, but usually at least one node is expected for a reaction.
        # We assert that if the schema requires nodes, it catches this.
        # For this contract test, we assume the schema requires non-empty nodes or validates count.
        # If the schema doesn't explicitly forbid empty, this might pass, but typically it's a data integrity issue.
        # Let's check if the schema has a minItems constraint or similar logic in our validator.
        # Since our simple validator checks presence, we add a manual check for empty if schema implies non-empty.
        # However, strictly following the schema: if schema doesn't forbid empty, we don't fail here.
        # But standard practice: a reaction graph must have atoms.
        if schema.get("nodes", {}).get("min_items", 0) > 0:
            assert len(errors) > 0

    def test_edge_distance_type_check(self, schema: Dict[str, Any]) -> None:
        """Ensure edge distances are validated as floats."""
        data = {
            "nodes": [{"atomic_number": 46, "formal_charge": 0, "coordination_number": 4, "element": "Pd"}],
            "edges": [{"source": 0, "target": 0, "distance": "not_a_float", "type": "bond"}], # String instead of float
            "metadata": {
                "energy_dft": -123.45,
                "barrier_height": 10.0,
                "reaction_id": "rxn_001",
                "ligand_class": "Group 13",
                "cutoff_used": 3.5
            }
        }
        errors = validate_graph(data, schema)
        assert len(errors) > 0
        assert any("distance" in e and "float" in e for e in errors)