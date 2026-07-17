"""Unit tests for CIF parsing logic in code/ingest/parse_cif.py.

This module verifies the robustness of the CIF parser, specifically focusing on:
1. Successful parsing of valid 2D structures.
2. Rejection of non-2D structures based on c-axis constraints.
3. Handling of disconnected graphs (structures with no bonds).
4. Graceful degradation when dependencies (pymatgen) are missing.
"""
import os
import tempfile
import json
from pathlib import Path
import numpy as np
import pytest

# Mock pymatgen if not available for testing in isolated envs, 
# but the test expects the real module to be present for full validation.
try:
    from pymatgen.core import Structure
    from pymatgen.analysis.graphs import StructureGraph
    HAS_PYMATGEN = True
except ImportError:
    HAS_PYMATGEN = False

# Import the module under test
from ingest.parse_cif import parse_cif_file, parse_cif_directory
from data_models.material_graph import MaterialGraph

@pytest.fixture
def sample_cif_content():
    """Sample CIF content for a simple 2D-like structure (Graphene slab)."""
    return """
    data_test_graphene
    _cell_length_a    2.46
    _cell_length_b    2.46
    _cell_length_c    20.0
    _cell_angle_alpha 90
    _cell_angle_beta  90
    _cell_angle_gamma 120
    _symmetry_space_group_name_H-M   P6/mmm
    _atom_site_label  C1
    _atom_site_type_symbol C
    _atom_site_fract_x 0.0
    _atom_site_fract_y 0.0
    _atom_site_fract_z 0.0
    _atom_site_label  C2
    _atom_site_type_symbol C
    _atom_site_fract_x 0.333333
    _atom_site_fract_y 0.666667
    _atom_site_fract_z 0.0
    """

@pytest.fixture
def sample_cif_file(tmp_path, sample_cif_content):
    """Creates a temporary CIF file."""
    cif_file = tmp_path / "graphene.cif"
    cif_file.write_text(sample_cif_content)
    return cif_file

@pytest.fixture
def sample_cif_dir(tmp_path, sample_cif_content):
    """Creates a temporary directory with CIF files."""
    cif1 = tmp_path / "graphene1.cif"
    cif1.write_text(sample_cif_content)
    
    # Add a non-2D structure (small c-axis)
    non_2d_content = """
    data_test_3d
    _cell_length_a    4.0
    _cell_length_b    4.0
    _cell_length_c    4.0
    _cell_angle_alpha 90
    _cell_angle_beta  90
    _cell_angle_gamma 90
    _atom_site_label  Si1
    _atom_site_type_symbol Si
    _atom_site_fract_x 0.0
    _atom_site_fract_y 0.0
    _atom_site_fract_z 0.0
    """
    cif2 = tmp_path / "silicon.cif"
    cif2.write_text(non_2d_content)
    return tmp_path

@pytest.mark.skipif(not HAS_PYMATGEN, reason="pymatgen not installed")
def test_parse_cif_file_success(sample_cif_file):
    """Test successful parsing of a valid 2D CIF file."""
    graph = parse_cif_file(sample_cif_file)
    
    assert graph is not None
    # The material_id is derived from the data_ block name or filename
    assert "graphene" in graph.material_id.lower()
    assert "C" in graph.composition
    assert len(graph.nodes) == 2
    # Graphene should have bonds, but we check for at least 1 to be safe
    assert len(graph.edges) >= 1
    # edge_index should be a numpy array with shape (2, num_edges)
    assert isinstance(graph.edge_index, np.ndarray)
    assert graph.edge_index.shape[0] == 2
    assert graph.space_group == "P6/mmm"
    
    # Verify node structure
    for node in graph.nodes:
        assert 'element' in node
        assert 'atomic_number' in node
        assert 'x' in node
        assert 'y' in node
        assert 'z' in node

@pytest.mark.skipif(not HAS_PYMATGEN, reason="pymatgen not installed")
def test_parse_cif_file_non_2d(sample_cif_dir):
    """Test that non-2D structures are filtered out."""
    silicon_path = sample_cif_dir / "silicon.cif"
    graph = parse_cif_file(silicon_path)
    
    # Should return None because c-axis is small (4.0 < 15.0)
    assert graph is None

@pytest.mark.skipif(not HAS_PYMATGEN, reason="pymatgen not installed")
def test_parse_cif_directory(sample_cif_dir):
    """Test parsing multiple CIF files from a directory."""
    graphs = parse_cif_directory(sample_cif_dir)
    
    # Should only return the 2D one (graphene)
    # The filename was graphene1.cif, so material_id should reflect that
    assert len(graphs) == 1
    assert "graphene1" in graphs[0].material_id

@pytest.mark.skipif(not HAS_PYMATGEN, reason="pymatgen not installed")
def test_disconnected_graph_handling(tmp_path):
    """Test handling of a structure with no bonds (disconnected).
    
    This test verifies that the parser does not crash when a structure
    results in an empty edge list (e.g., atoms too far apart for the
    default bonding algorithm).
    """
    # Create a CIF with atoms far apart (no bonds formed by MinimumDistanceNN)
    content = """
    data_test_disconnected
    _cell_length_a    10.0
    _cell_length_b    10.0
    _cell_length_c    20.0
    _cell_angle_alpha 90
    _cell_angle_beta  90
    _cell_angle_gamma 90
    _atom_site_label  H1
    _atom_site_type_symbol H
    _atom_site_fract_x 0.0
    _atom_site_fract_y 0.0
    _atom_site_fract_z 0.0
    _atom_site_label  H2
    _atom_site_type_symbol H
    _atom_site_fract_x 0.9
    _atom_site_fract_y 0.9
    _atom_site_fract_z 0.0
    """
    cif_file = tmp_path / "disconnected.cif"
    cif_file.write_text(content)
    
    # This might still bond if distance is within cutoff, but we test robustness
    # The key is that it doesn't crash.
    graph = parse_cif_file(cif_file)
    
    # If it returns a graph, verify edge_index shape is correct even if empty
    if graph is not None:
        assert isinstance(graph.edge_index, np.ndarray)
        # Even if empty, shape should be (2, 0)
        assert graph.edge_index.shape[0] == 2

def test_parse_cif_file_missing_pymatgen(monkeypatch):
    """Test behavior when pymatgen is not installed."""
    # We simulate the missing dependency by patching the import in the module
    import ingest.parse_cif as parse_module
    
    # Save original
    original_structure = getattr(parse_module, 'Structure', None)
    original_graph = getattr(parse_module, 'StructureGraph', None)
    
    # Simulate failure by setting to None or raising ImportError on access
    # The safest way to test the 'if HAS_PYMATGEN' block logic is to patch the check
    # But since we can't easily patch the module-level variable after import,
    # we rely on the fact that the code should handle the ImportError during import
    # or the HAS_PYMATGEN flag.
    
    # For this test, we assume the module has a fallback or returns None.
    # If the module crashes on import without pymatgen, this test would need
    # to be run in an environment without pymatgen.
    # Here we test the logic path where the function returns None if deps missing.
    
    # Mock the internal check
    parse_module.HAS_PYMATGEN = False
    
    try:
        with tempfile.NamedTemporaryFile(suffix=".cif", delete=False) as f:
            f.write(b"data\n")
            temp_path = Path(f.name)
        
        result = parse_cif_file(temp_path)
        assert result is None
        
        os.unlink(temp_path)
    finally:
        # Restore
        parse_module.HAS_PYMATGEN = True