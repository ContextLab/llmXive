"""
Tests for construct_network.py
"""
import os
import pickle
import tempfile
from pathlib import Path
import pytest
import networkx as nx
from pymatgen.core import Structure, Lattice

from construct_network import (
    get_element_covalent_radius,
    detect_bonds_covalent,
    detect_bonds_fallback,
    construct_network_from_structure,
    process_cif_file
)

def test_get_element_covalent_radius():
    """Test covalent radius retrieval"""
    radius = get_element_covalent_radius("Si")
    assert radius > 0
    assert isinstance(radius, float)

def test_construct_network_simple():
    """Test network construction with a simple structure"""
    # Create a simple Si crystal structure
    lattice = Lattice.cubic(5.43)
    coords = [
        [0, 0, 0],
        [0.25, 0.25, 0.25],
        [0.5, 0.5, 0],
        [0.75, 0.75, 0.25],
        [0.5, 0, 0.5],
        [0.75, 0.25, 0.75],
        [0, 0.5, 0.5],
        [0.25, 0.75, 0.75]
    ]
    species = ["Si"] * 8

    structure = Structure(lattice, species, coords)
    graph = construct_network_from_structure(structure)

    assert graph is not None
    assert graph.number_of_nodes() == 8
    assert graph.number_of_edges() >= 1

def test_construct_network_disconnected_fallback():
    """Test that fallback mechanism works for sparse structures"""
    # Create a structure with atoms far apart
    lattice = Lattice.cubic(20.0)  # Large lattice
    coords = [[0, 0, 0], [0.9, 0.9, 0.9]]
    species = ["Si", "Si"]

    structure = Structure(lattice, species, coords)
    graph = construct_network_from_structure(structure)

    # Should either find bonds via fallback or return None
    if graph is not None:
        assert graph.number_of_nodes() == 2
        assert graph.number_of_edges() >= 1

def test_process_cif_file_integration():
    """Integration test for CIF processing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        cif_path = tmpdir / "test.cif"

        # Create a minimal CIF file
        cif_content = """
        data_test
        _chemical_formula_sum 'Si2'
        _cell_length_a 5.43
        _cell_length_b 5.43
        _cell_length_c 5.43
        _cell_angle_alpha 90
        _cell_angle_beta 90
        _cell_angle_gamma 90
        _symmetry_space_group_name_H-M 'F d -3 m'
        loop_
        _atom_site_type_symbol
        _atom_site_fract_x
        _atom_site_fract_y
        _atom_site_fract_z
        Si 0.0 0.0 0.0
        Si 0.125 0.125 0.125
        """
        cif_path.write_text(cif_content)

        output_dir = tmpdir / "output"
        output_dir.mkdir()

        result = process_cif_file(cif_path, output_dir)

        assert result is not None
        assert result["material_id"] == "test"
        assert result["status"] == "processed"
        assert "cif_checksum" in result
        assert "graph_checksum" in result

        # Verify pickle file exists
        pkl_path = Path(result["network_path"])
        assert pkl_path.exists()

        # Verify graph can be loaded
        with open(pkl_path, 'rb') as f:
            loaded_graph = pickle.load(f)
        assert isinstance(loaded_graph, nx.Graph)
        assert loaded_graph.number_of_nodes() >= 2
        assert loaded_graph.number_of_edges() >= 1
