"""
Unit tests for CIF parsing functionality.

Tests cover:
- Valid CIF parsing
- Disconnected graph handling
- Invalid CIF handling
- Feature extraction correctness
"""

import os
import tempfile
from pathlib import Path
import numpy as np
import pytest

from code.ingest.parse_cif import parse_cif_to_graph, parse_multiple_cifs
from code.data_models.material_graph import MaterialGraph


@pytest.fixture
def sample_cif_content():
    """Sample CIF content for a simple 2D material (graphene-like)."""
    return """
    data_sample_graphene
    _chemical_formula_sum 'C2'
    _cell_length_a 2.46
    _cell_length_b 2.46
    _cell_length_c 10.0
    _cell_angle_alpha 90
    _cell_angle_beta 90
    _cell_angle_gamma 120
    _symmetry_space_group_name_H-M 'P6/mmm'

    loop_
    _atom_site_label
    _atom_site_type_symbol
    _atom_site_fract_x
    _atom_site_fract_y
    _atom_site_fract_z
    C1 C 0.0 0.0 0.0
    C2 C 0.333 0.667 0.0
    """

@pytest.fixture
def sample_cif_disconnected():
    """Sample CIF with disconnected components (molecules far apart)."""
    return """
    data_disconnected
    _chemical_formula_sum 'C2 O2'
    _cell_length_a 10.0
    _cell_length_b 10.0
    _cell_length_c 10.0
    _cell_angle_alpha 90
    _cell_angle_beta 90
    _cell_angle_gamma 90
    _symmetry_space_group_name_H-M 'P1'

    loop_
    _atom_site_label
    _atom_site_type_symbol
    _atom_site_fract_x
    _atom_site_fract_y
    _atom_site_fract_z
    C1 C 0.1 0.1 0.5
    C2 C 0.15 0.15 0.5
    O1 O 0.8 0.8 0.5
    O2 O 0.85 0.85 0.5
    """

@pytest.fixture
def invalid_cif_content():
    """Invalid CIF content (missing required fields)."""
    return """
    data_invalid
    _chemical_formula_sum 'C'
    _cell_length_a -1.0
    _cell_length_b 2.46
    _cell_length_c 10.0
    """

def test_parse_valid_cif(sample_cif_content, tmp_path):
    """Test parsing a valid CIF file."""
    cif_file = tmp_path / "graphene.cif"
    cif_file.write_text(sample_cif_content)

    graph = parse_cif_to_graph(cif_file)

    assert graph is not None
    assert graph.material_id is not None
    assert len(graph.node_features) == 2
    assert graph.composition == "C2"
    assert graph.structure_info["num_atoms"] == 2
    assert "lattice_parameters" in graph.structure_info


def test_parse_disconnected_graph(sample_cif_disconnected, tmp_path):
    """Test handling of disconnected graph (molecules far apart)."""
    cif_file = tmp_path / "disconnected.cif"
    cif_file.write_text(sample_cif_disconnected)

    graph = parse_cif_to_graph(cif_file)

    # Should still parse, but may have disconnected components
    assert graph is not None
    assert len(graph.node_features) == 4

    # Check that adjacency matrix reflects connectivity
    # In a disconnected system, some nodes may have no edges
    assert graph.adjacency_matrix.shape == (4, 4)


def test_parse_invalid_cif(invalid_cif_content, tmp_path, caplog):
    """Test parsing an invalid CIF file."""
    cif_file = tmp_path / "invalid.cif"
    cif_file.write_text(invalid_cif_content)

    graph = parse_cif_to_graph(cif_file)

    # Should return None for invalid structure
    assert graph is None


def test_parse_nonexistent_file(tmp_path):
    """Test parsing a non-existent file."""
    non_existent = tmp_path / "does_not_exist.cif"

    graph = parse_cif_to_graph(non_existent)

    assert graph is None


def test_node_features_structure(sample_cif_content, tmp_path):
    """Test that node features have correct structure and types."""
    cif_file = tmp_path / "graphene.cif"
    cif_file.write_text(sample_cif_content)

    graph = parse_cif_to_graph(cif_file)

    assert graph.node_features is not None
    assert len(graph.node_features) == 2

    # Check first node features
    node = graph.node_features[0]
    assert "atomic_number" in node
    assert "atomic_mass" in node
    assert "electronegativity" in node
    assert "covalent_radius" in node
    assert "coordination_number" in node
    assert "fractional_x" in node

    # Verify numeric types
    assert isinstance(node["atomic_number"], float)
    assert isinstance(node["fractional_x"], float)


def test_edge_features_exist(sample_cif_content, tmp_path):
    """Test that edge features are extracted when bonds exist."""
    cif_file = tmp_path / "graphene.cif"
    cif_file.write_text(sample_cif_content)

    graph = parse_cif_to_graph(cif_file)

    # Graphene should have bonds
    assert graph.edge_indices is not None
    assert graph.edge_features is not None


def test_multiple_cif_parsing(sample_cif_content, tmp_path):
    """Test parsing multiple CIF files."""
    # Create multiple CIF files
    for i in range(3):
        cif_file = tmp_path / f"graphene_{i}.cif"
        cif_file.write_text(sample_cif_content)

    graphs = parse_multiple_cifs(tmp_path)

    assert len(graphs) == 3
    assert all(isinstance(g, MaterialGraph) for g in graphs)


def test_empty_directory(tmp_path):
    """Test parsing from an empty directory."""
    graphs = parse_multiple_cifs(tmp_path)

    assert len(graphs) == 0


def test_max_files_limit(sample_cif_content, tmp_path):
    """Test max_files parameter limits parsing."""
    for i in range(5):
        cif_file = tmp_path / f"graphene_{i}.cif"
        cif_file.write_text(sample_cif_content)

    graphs = parse_multiple_cifs(tmp_path, max_files=2)

    assert len(graphs) == 2


def test_coordination_number_computation(sample_cif_content, tmp_path):
    """Test that coordination numbers are computed correctly."""
    cif_file = tmp_path / "graphene.cif"
    cif_file.write_text(sample_cif_content)

    graph = parse_cif_to_graph(cif_file)

    # Graphene carbon atoms should have coordination number of 3
    for node in graph.node_features:
        assert "coordination_number" in node
        # In graphene, each C has 3 neighbors
        assert node["coordination_number"] == 3.0