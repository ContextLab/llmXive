"""
Contract tests for TransitionStateGraph schema validation.

This module validates that graph data conforms to the schema defined in
code/contracts/dataset_graph.schema.yaml.

Dependencies:
  - T008: code/contracts/dataset_graph.schema.yaml
  - T018: code/src/data/validate_graphs.py (provides validation logic)
"""
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import pytest

# Import the validation logic from the project
from code.src.data.validate_graphs import (
    GraphValidationError,
    load_schema,
    validate_node_attributes,
    validate_edge_attributes,
    validate_graph_metadata,
    validate_graph_structure,
    validate_graph,
    validate_all_graphs,
    get_project_root
)


class TestGraphSchemaValidation:
    """Test cases for validating TransitionStateGraph against the schema."""

    @pytest.fixture
    def schema_path(self) -> Path:
        """Return the path to the graph schema file."""
        return get_project_root() / "contracts" / "dataset_graph.schema.yaml"

    @pytest.fixture
    def valid_node_data(self) -> pd.DataFrame:
        """Create valid node attributes DataFrame."""
        return pd.DataFrame([
            {
                "atomic_number": 46,  # Pd
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "is_metal": True,
                "ligand_class": "Conventional",
                "formal_charge": 0
            },
            {
                "atomic_number": 6,  # C
                "x": 1.5,
                "y": 0.0,
                "z": 0.0,
                "is_metal": False,
                "ligand_class": "Conventional",
                "formal_charge": 0
            }
        ])

    @pytest.fixture
    def valid_edge_data(self) -> pd.DataFrame:
        """Create valid edge attributes DataFrame."""
        return pd.DataFrame([
            {
                "source": 0,
                "target": 1,
                "distance": 1.5,
                "edge_type": "covalent"
            }
        ])

    @pytest.fixture
    def valid_metadata(self) -> Dict[str, Any]:
        """Create valid graph metadata."""
        return {
            "energy_dft": -1234.567,
            "barrier_height": 15.2,
            "metal_center": 46,
            "ligand_class": "Conventional",
            "reaction_id": "test_reaction_001",
            "geometry_source": "QM9-TS",
            "is_outlier": False,
            "cutoff_used": 3.5
        }

    @pytest.fixture
    def valid_graph_data(
        self,
        valid_node_data: pd.DataFrame,
        valid_edge_data: pd.DataFrame,
        valid_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a complete valid graph data structure."""
        return {
            "node_attributes": valid_node_data,
            "edge_attributes": valid_edge_data,
            "graph_metadata": valid_metadata
        }

    def test_load_schema_valid(self, schema_path: Path) -> None:
        """Test that the schema file can be loaded successfully."""
        assert schema_path.exists(), f"Schema file not found at {schema_path}"
        schema = load_schema(schema_path)
        assert schema is not None
        assert "properties" in schema
        assert "node_attributes" in schema["properties"]
        assert "edge_attributes" in schema["properties"]
        assert "graph_metadata" in schema["properties"]

    def test_load_schema_missing_file(self) -> None:
        """Test that loading a missing schema file raises an error."""
        fake_path = Path("/nonexistent/path/schema.yaml")
        with pytest.raises(FileNotFoundError):
            load_schema(fake_path)

    # --- Node Attribute Tests ---

    def test_validate_node_attributes_valid(self, valid_node_data: pd.DataFrame) -> None:
        """Test validation of valid node attributes."""
        # Load schema to get requirements
        schema_path = get_project_root() / "contracts" / "dataset_graph.schema.yaml"
        schema = load_schema(schema_path)
        
        # This should not raise
        result = validate_node_attributes(valid_node_data, schema["properties"]["node_attributes"])
        assert result is None or result == []

    def test_validate_node_attributes_missing_column(self) -> None:
        """Test validation fails when required node column is missing."""
        schema_path = get_project_root() / "contracts" / "dataset_graph.schema.yaml"
        schema = load_schema(schema_path)
        
        # Create data missing 'atomic_number'
        invalid_data = pd.DataFrame([
            {"x": 0.0, "y": 0.0, "z": 0.0}
        ])
        
        with pytest.raises(GraphValidationError) as exc_info:
            validate_node_attributes(invalid_data, schema["properties"]["node_attributes"])
        assert "atomic_number" in str(exc_info.value)

    def test_validate_node_attributes_wrong_type(self) -> None:
        """Test validation fails when node column has wrong type."""
        schema_path = get_project_root() / "contracts" / "dataset_graph.schema.yaml"
        schema = load_schema(schema_path)
        
        # Create data with wrong type for atomic_number (string instead of int)
        invalid_data = pd.DataFrame([
            {
                "atomic_number": "not_an_int",
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "is_metal": True,
                "ligand_class": "Conventional",
                "formal_charge": 0
            }
        ])
        
        with pytest.raises(GraphValidationError) as exc_info:
            validate_node_attributes(invalid_data, schema["properties"]["node_attributes"])
        assert "atomic_number" in str(exc_info.value)

    def test_validate_node_attributes_invalid_ligand_class(self) -> None:
        """Test validation fails when ligand_class is not in enum."""
        schema_path = get_project_root() / "contracts" / "dataset_graph.schema.yaml"
        schema = load_schema(schema_path)
        
        invalid_data = pd.DataFrame([
            {
                "atomic_number": 46,
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "is_metal": True,
                "ligand_class": "InvalidClass",  # Not in enum
                "formal_charge": 0
            }
        ])
        
        with pytest.raises(GraphValidationError) as exc_info:
            validate_node_attributes(invalid_data, schema["properties"]["node_attributes"])
        assert "ligand_class" in str(exc_info.value)

    # --- Edge Attribute Tests ---

    def test_validate_edge_attributes_valid(self, valid_edge_data: pd.DataFrame) -> None:
        """Test validation of valid edge attributes."""
        schema_path = get_project_root() / "contracts" / "dataset_graph.schema.yaml"
        schema = load_schema(schema_path)
        
        result = validate_edge_attributes(valid_edge_data, schema["properties"]["edge_attributes"])
        assert result is None or result == []

    def test_validate_edge_attributes_missing_column(self) -> None:
        """Test validation fails when required edge column is missing."""
        schema_path = get_project_root() / "contracts" / "dataset_graph.schema.yaml"
        schema = load_schema(schema_path)
        
        invalid_data = pd.DataFrame([
            {"source": 0, "distance": 1.5}  # Missing 'target'
        ])
        
        with pytest.raises(GraphValidationError) as exc_info:
            validate_edge_attributes(invalid_data, schema["properties"]["edge_attributes"])
        assert "target" in str(exc_info.value)

    def test_validate_edge_attributes_wrong_type(self) -> None:
        """Test validation fails when edge column has wrong type."""
        schema_path = get_project_root() / "contracts" / "dataset_graph.schema.yaml"
        schema = load_schema(schema_path)
        
        invalid_data = pd.DataFrame([
            {
                "source": "not_an_int",  # Should be int
                "target": 1,
                "distance": 1.5,
                "edge_type": "covalent"
            }
        ])
        
        with pytest.raises(GraphValidationError) as exc_info:
            validate_edge_attributes(invalid_data, schema["properties"]["edge_attributes"])
        assert "source" in str(exc_info.value)

    def test_validate_edge_attributes_invalid_edge_type(self) -> None:
        """Test validation fails when edge_type is not in enum."""
        schema_path = get_project_root() / "contracts" / "dataset_graph.schema.yaml"
        schema = load_schema(schema_path)
        
        invalid_data = pd.DataFrame([
            {
                "source": 0,
                "target": 1,
                "distance": 1.5,
                "edge_type": "invalid_type"  # Not in enum
            }
        ])
        
        with pytest.raises(GraphValidationError) as exc_info:
            validate_edge_attributes(invalid_data, schema["properties"]["edge_attributes"])
        assert "edge_type" in str(exc_info.value)

    # --- Graph Metadata Tests ---

    def test_validate_graph_metadata_valid(self, valid_metadata: Dict[str, Any]) -> None:
        """Test validation of valid graph metadata."""
        schema_path = get_project_root() / "contracts" / "dataset_graph.schema.yaml"
        schema = load_schema(schema_path)
        
        result = validate_graph_metadata(valid_metadata, schema["properties"]["graph_metadata"])
        assert result is None or result == []

    def test_validate_graph_metadata_missing_field(self) -> None:
        """Test validation fails when required metadata field is missing."""
        schema_path = get_project_root() / "contracts" / "dataset_graph.schema.yaml"
        schema = load_schema(schema_path)
        
        invalid_metadata = {
            "energy_dft": -1234.567,
            "barrier_height": 15.2,
            # Missing metal_center
            "ligand_class": "Conventional",
            "reaction_id": "test_001",
            "geometry_source": "QM9-TS",
            "is_outlier": False,
            "cutoff_used": 3.5
        }
        
        with pytest.raises(GraphValidationError) as exc_info:
            validate_graph_metadata(invalid_metadata, schema["properties"]["graph_metadata"])
        assert "metal_center" in str(exc_info.value)

    def test_validate_graph_metadata_wrong_type(self) -> None:
        """Test validation fails when metadata field has wrong type."""
        schema_path = get_project_root() / "contracts" / "dataset_graph.schema.yaml"
        schema = load_schema(schema_path)
        
        invalid_metadata = {
            "energy_dft": -1234.567,
            "barrier_height": 15.2,
            "metal_center": "not_an_int",  # Should be int
            "ligand_class": "Conventional",
            "reaction_id": "test_001",
            "geometry_source": "QM9-TS",
            "is_outlier": False,
            "cutoff_used": 3.5
        }
        
        with pytest.raises(GraphValidationError) as exc_info:
            validate_graph_metadata(invalid_metadata, schema["properties"]["graph_metadata"])
        assert "metal_center" in str(exc_info.value)

    def test_validate_graph_metadata_invalid_ligand_class(self) -> None:
        """Test validation fails when metadata ligand_class is invalid."""
        schema_path = get_project_root() / "contracts" / "dataset_graph.schema.yaml"
        schema = load_schema(schema_path)
        
        invalid_metadata = {
            "energy_dft": -1234.567,
            "barrier_height": 15.2,
            "metal_center": 46,
            "ligand_class": "InvalidClass",  # Not in enum
            "reaction_id": "test_001",
            "geometry_source": "QM9-TS",
            "is_outlier": False,
            "cutoff_used": 3.5
        }
        
        with pytest.raises(GraphValidationError) as exc_info:
            validate_graph_metadata(invalid_metadata, schema["properties"]["graph_metadata"])
        assert "ligand_class" in str(exc_info.value)

    # --- Graph Structure Tests ---

    def test_validate_graph_structure_valid(
        self,
        valid_node_data: pd.DataFrame,
        valid_edge_data: pd.DataFrame
    ) -> None:
        """Test validation of valid graph structure."""
        # This should not raise
        result = validate_graph_structure(valid_node_data, valid_edge_data)
        assert result is None or result == []

    def test_validate_graph_structure_self_loops_disallowed(self) -> None:
        """Test validation fails when self-loops are present."""
        nodes = pd.DataFrame([
            {"atomic_number": 46, "x": 0.0, "y": 0.0, "z": 0.0, "is_metal": True, "ligand_class": "Conventional", "formal_charge": 0}
        ])
        edges = pd.DataFrame([
            {"source": 0, "target": 0, "distance": 0.0, "edge_type": "covalent"}  # Self-loop
        ])
        
        with pytest.raises(GraphValidationError) as exc_info:
            validate_graph_structure(nodes, edges)
        assert "self-loop" in str(exc_info.value).lower()

    def test_validate_graph_structure_invalid_edge_references(self) -> None:
        """Test validation fails when edge references non-existent node."""
        nodes = pd.DataFrame([
            {"atomic_number": 46, "x": 0.0, "y": 0.0, "z": 0.0, "is_metal": True, "ligand_class": "Conventional", "formal_charge": 0}
        ])
        edges = pd.DataFrame([
            {"source": 0, "target": 99, "distance": 1.5, "edge_type": "covalent"}  # Target 99 doesn't exist
        ])
        
        with pytest.raises(GraphValidationError) as exc_info:
            validate_graph_structure(nodes, edges)
        assert "edge" in str(exc_info.value).lower()

    # --- Full Graph Validation Tests ---

    def test_validate_graph_full_valid(self, valid_graph_data: Dict[str, Any]) -> None:
        """Test validation of a complete valid graph."""
        schema_path = get_project_root() / "contracts" / "dataset_graph.schema.yaml"
        schema = load_schema(schema_path)
        
        # This should not raise
        result = validate_graph(valid_graph_data, schema)
        assert result is None or result == []

    def test_validate_graph_full_invalid(self) -> None:
        """Test validation fails for a graph with invalid node attributes."""
        schema_path = get_project_root() / "contracts" / "dataset_graph.schema.yaml"
        schema = load_schema(schema_path)
        
        invalid_data = {
            "node_attributes": pd.DataFrame([
                {"x": 0.0, "y": 0.0, "z": 0.0}  # Missing required columns
            ]),
            "edge_attributes": pd.DataFrame([
                {"source": 0, "target": 1, "distance": 1.5, "edge_type": "covalent"}
            ]),
            "graph_metadata": {
                "energy_dft": -1234.567,
                "barrier_height": 15.2,
                "metal_center": 46,
                "ligand_class": "Conventional",
                "reaction_id": "test_001",
                "geometry_source": "QM9-TS",
                "is_outlier": False,
                "cutoff_used": 3.5
            }
        }
        
        with pytest.raises(GraphValidationError):
            validate_graph(invalid_data, schema)

    # --- Batch Validation Tests ---

    def test_validate_all_graphs_valid(
        self,
        valid_graph_data: Dict[str, Any]
    ) -> None:
        """Test validation of a list of valid graphs."""
        schema_path = get_project_root() / "contracts" / "dataset_graph.schema.yaml"
        schema = load_schema(schema_path)
        
        graphs = [valid_graph_data, valid_graph_data]
        
        # This should not raise
        result = validate_all_graphs(graphs, schema)
        assert result is None or result == []

    def test_validate_all_graphs_mixed(self, valid_graph_data: Dict[str, Any]) -> None:
        """Test validation fails when list contains at least one invalid graph."""
        schema_path = get_project_root() / "contracts" / "dataset_graph.schema.yaml"
        schema = load_schema(schema_path)
        
        invalid_graph = {
            "node_attributes": pd.DataFrame([{"x": 0.0}]),  # Invalid
            "edge_attributes": pd.DataFrame([]),
            "graph_metadata": {
                "energy_dft": -1234.567,
                "barrier_height": 15.2,
                "metal_center": 46,
                "ligand_class": "Conventional",
                "reaction_id": "test_001",
                "geometry_source": "QM9-TS",
                "is_outlier": False,
                "cutoff_used": 3.5
            }
        }
        
        graphs = [valid_graph_data, invalid_graph]
        
        with pytest.raises(GraphValidationError):
            validate_all_graphs(graphs, schema)