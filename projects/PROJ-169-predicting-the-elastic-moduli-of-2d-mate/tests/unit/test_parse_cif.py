import json
import tempfile
from pathlib import Path
import pytest
import numpy as np

from ingest.parse_cif import parse_cif_file, parse_cif_directory, get_atomic_properties
from data_models.material_graph import MaterialGraph


# Sample CIF content for a simple 2D-like structure (graphene sheet approximation)
SAMPLE_CIF_CONTENT = """
data_test_graphene
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
C2 C 0.333333 0.666667 0.0
"""

# Sample CIF with disconnected atoms (far apart) to test edge handling
SAMPLE_CIF_DISCONNECTED = """
data_test_disconnected
_chemical_formula_sum 'C2'
_cell_length_a 20.0
_cell_length_b 20.0
_cell_length_c 20.0
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
C1 C 0.0 0.0 0.0
C2 C 0.9 0.9 0.9
"""

def test_get_atomic_properties_valid():
    props = get_atomic_properties("C")
    assert "atomic_number" in props
    assert "atomic_mass" in props
    assert props["atomic_number"] == 6  # Carbon

def test_get_atomic_properties_invalid():
    props = get_atomic_properties("X")
    # Should return defaults (0.0) without crashing
    assert props["atomic_number"] == 0
    assert props["atomic_mass"] == 0.0

def test_parse_cif_file_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        cif_path = Path(tmpdir) / "test.cif"
        cif_path.write_text(SAMPLE_CIF_CONTENT)

        graph = parse_cif_file(cif_path)

        assert graph is not None
        assert graph.source_id == "test"
        assert len(graph.node_features) == 2
        assert len(graph.edge_indices) > 0  # Should have edges
        assert graph.node_features.shape[1] > 0  # Features exist

def test_parse_cif_file_disconnected_graph():
    with tempfile.TemporaryDirectory() as tmpdir:
        cif_path = Path(tmpdir) / "test_disconnected.cif"
        cif_path.write_text(SAMPLE_CIF_DISCONNECTED)

        graph = parse_cif_file(cif_path)

        assert graph is not None
        # With a 20x20x20 cell and atoms at corners, distance is large (~17 Angstroms)
        # If cutoff is 5.0, there should be NO edges
        assert len(graph.node_features) == 2
        # Edge Indices should be empty or very small if cutoff is strict
        # Our implementation uses a 5.0 Angstrom cutoff.
        # Distance in Cartesian:
        # frac (0,0,0) -> cart (0,0,0)
        # frac (0.9, 0.9, 0.9) -> cart (18, 18, 18) approx
        # Dist ~ 31 Angstroms. No edges expected.
        assert len(graph.edge_indices) == 0

def test_parse_cif_file_missing_file():
    graph = parse_cif_file(Path("non_existent.cif"))
    assert graph is None

def test_parse_cif_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "a.cif").write_text(SAMPLE_CIF_CONTENT)
        (tmp_path / "b.cif").write_text(SAMPLE_CIF_CONTENT)
        (tmp_path / "c.txt").write_text("not a cif")

        graphs = parse_cif_directory(tmp_path)

        assert len(graphs) == 2
        for g in graphs:
            assert isinstance(g, MaterialGraph)

def test_parse_cif_directory_recursive():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (subdir / "a.cif").write_text(SAMPLE_CIF_CONTENT)

        graphs = parse_cif_directory(tmp_path, recursive=True)
        assert len(graphs) == 1

def test_parse_cif_file_invalid_content():
    with tempfile.TemporaryDirectory() as tmpdir:
        cif_path = Path(tmpdir) / "invalid.cif"
        cif_path.write_text("This is not a valid CIF file content")

        graph = parse_cif_file(cif_path)
        assert graph is None

def test_material_graph_structure():
    """Verify that the generated MaterialGraph has correct numpy types and shapes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cif_path = Path(tmpdir) / "test.cif"
        cif_path.write_text(SAMPLE_CIF_CONTENT)

        graph = parse_cif_file(cif_path)

        assert isinstance(graph.node_features, np.ndarray)
        assert isinstance(graph.edge_indices, np.ndarray)
        assert isinstance(graph.edge_features, np.ndarray)
        
        # Check dtypes
        assert graph.node_features.dtype == np.float32
        assert graph.edge_indices.dtype == np.int64
        assert graph.edge_features.dtype == np.float32