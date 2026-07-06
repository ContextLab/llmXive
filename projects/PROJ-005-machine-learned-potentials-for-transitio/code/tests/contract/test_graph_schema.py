"""
Contract test for graph schema validation (T012/T019).

This test ensures that the validation logic in src.data.validate_graphs
correctly rejects graphs that do not conform to the schema defined in
contracts/dataset_graph.schema.yaml.
"""
import pandas as pd
import pytest
from pathlib import Path
import tempfile
import json
import numpy as np

from src.data.validate_graphs import (
    validate_graph,
    validate_node_attributes,
    validate_edge_attributes,
    validate_graph_metadata,
    GraphValidationError
)

class TestGraphSchemaValidation:
    """Tests for the graph schema validation logic."""

    def test_valid_node_attributes(self):
        """Test that valid node attributes pass validation."""
        data = {
            "atomic_number": [6, 7, 8],
            "formal_charge": [0, 0, 0],
            "ligand_class": ["Group 13", "Conventional", "Conventional"]
        }
        df = pd.DataFrame(data)
        errors = validate_node_attributes(df)
        assert len(errors) == 0

    def test_missing_node_attribute(self):
        """Test that missing node attributes fail validation."""
        data = {
            "atomic_number": [6, 7],
            "formal_charge": [0, 0]
            # Missing 'ligand_class'
        }
        df = pd.DataFrame(data)
        errors = validate_node_attributes(df)
        assert len(errors) == 1
        assert "ligand_class" in errors[0]

    def test_invalid_ligand_class(self):
        """Test that invalid ligand_class values fail validation."""
        data = {
            "atomic_number": [6],
            "formal_charge": [0],
            "ligand_class": ["InvalidClass"]
        }
        df = pd.DataFrame(data)
        errors = validate_node_attributes(df)
        assert len(errors) == 1
        assert "InvalidClass" in errors[0]

    def test_valid_edge_attributes(self):
        """Test that valid edge attributes pass validation."""
        data = {
            "distance": [1.5, 2.0],
            "edge_type": ["covalent", "hydrogen"]
        }
        df = pd.DataFrame(data)
        errors = validate_edge_attributes(df)
        assert len(errors) == 0

    def test_missing_edge_attribute(self):
        """Test that missing edge attributes fail validation."""
        data = {
            "distance": [1.5],
            # Missing 'edge_type'
        }
        df = pd.DataFrame(data)
        errors = validate_edge_attributes(df)
        assert len(errors) == 1

    def test_valid_graph_metadata(self):
        """Test that valid metadata passes validation."""
        metadata = {
            "energy_dft": -123.45,
            "barrier_height": 15.2
        }
        errors = validate_graph_metadata(metadata)
        assert len(errors) == 0

    def test_missing_graph_metadata(self):
        """Test that missing metadata keys fail validation."""
        metadata = {
            "energy_dft": -123.45
            # Missing 'barrier_height'
        }
        errors = validate_graph_metadata(metadata)
        assert len(errors) == 1
        assert "barrier_height" in errors[0]

    def test_invalid_graph_metadata_type(self):
        """Test that invalid metadata types fail validation."""
        metadata = {
            "energy_dft": "not_a_float",
            "barrier_height": 15.2
        }
        errors = validate_graph_metadata(metadata)
        assert len(errors) == 1
        assert "energy_dft" in errors[0]

    def test_edge_index_out_of_bounds(self):
        """Test that edge indices exceeding node count fail validation."""
        nodes_df = pd.DataFrame({
            "atomic_number": [6, 7],
            "formal_charge": [0, 0],
            "ligand_class": ["Group 13", "Conventional"]
        })
        edges_df = pd.DataFrame({
            "source": [0, 2],  # 2 is out of bounds for 2 nodes
            "target": [1, 0],
            "distance": [1.5, 1.6],
            "edge_type": ["covalent", "covalent"]
        })
        metadata = {"energy_dft": 1.0, "barrier_height": 1.0}
        
        is_valid, errors = validate_graph(nodes_df, edges_df, metadata)
        assert not is_valid
        assert any("exceed" in err for err in errors)

    def test_full_graph_validation_success(self):
        """Test a fully valid graph structure."""
        nodes_df = pd.DataFrame({
            "atomic_number": [6, 7, 8],
            "formal_charge": [0, 0, 0],
            "ligand_class": ["Group 13", "Conventional", "Conventional"]
        })
        edges_df = pd.DataFrame({
            "source": [0, 1],
            "target": [1, 2],
            "distance": [1.5, 1.6],
            "edge_type": ["covalent", "covalent"]
        })
        metadata = {"energy_dft": -123.45, "barrier_height": 15.2}
        
        is_valid, errors = validate_graph(nodes_df, edges_df, metadata)
        assert is_valid
        assert len(errors) == 0

    def test_full_graph_validation_failure(self):
        """Test a graph that fails validation."""
        nodes_df = pd.DataFrame({
            "atomic_number": [6, 7],
            "formal_charge": [0, 0],
            "ligand_class": ["Invalid"]
        })
        edges_df = pd.DataFrame({
            "source": [0, 1],
            "target": [1, 0],
            "distance": [1.5, 1.6],
            "edge_type": ["covalent", "covalent"]
        })
        metadata = {"energy_dft": -123.45, "barrier_height": 15.2}
        
        is_valid, errors = validate_graph(nodes_df, edges_df, metadata)
        assert not is_valid
        assert len(errors) > 0
        assert any("Invalid" in err for err in errors)
