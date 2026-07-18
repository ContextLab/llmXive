"""
Unit tests for CIF parsing logic (T010).
Verifies disconnected graph handling and feature extraction.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

# Ensure imports work from tests directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest.parse_cif import parse_cif_file, parse_cif_directory, NODE_FEATURES
from data_models.material_graph import MaterialGraph
import numpy as np

# Sample CIF content for a simple structure (Silicon)
SAMPLE_CIF_SILICON = """
data_Si
_cell_length_a    5.43
_cell_length_b    5.43
_cell_length_c    5.43
_cell_angle_alpha 90
_cell_angle_beta  90
_cell_angle_gamma 90
_symmetry_space_group_name_H-M 'F d -3 m'
_symmetry_Int_Tables_number 227

loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
Si1 Si 0.0 0.0 0.0
Si2 Si 0.25 0.25 0.25
Si3 Si 0.5 0.5 0.0
Si4 Si 0.75 0.75 0.25
Si5 Si 0.5 0.0 0.5
Si6 Si 0.75 0.25 0.75
Si7 Si 0.0 0.5 0.5
Si8 Si 0.25 0.75 0.75
"""

# Sample CIF with disconnected components (hypothetical for testing)
# Note: pymatgen might merge them or treat as one structure with large vacuum.
# We test that the parser doesn't crash on unusual connectivity.
SAMPLE_CIF_DISCONNECTED = """
data_Disconnected
_cell_length_a    20.0
_cell_length_b    20.0
_cell_length_c    20.0
_cell_angle_alpha 90
_cell_angle_beta  90
_cell_angle_gamma 90
_symmetry_space_group_name_H-M 'P 1'
_symmetry_Int_Tables_number 1

loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
C1 C 0.1 0.1 0.1
C2 C 0.9 0.9 0.9
# Atoms are far apart, likely no bonds
"""

@pytest.fixture
def temp_cif_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Write sample files
        (tmpdir / "si.cif").write_text(SAMPLE_CIF_SILICON)
        (tmpdir / "disconnected.cif").write_text(SAMPLE_CIF_DISCONNECTED)
        yield tmpdir

def test_parse_valid_cif(temp_cif_dir):
    """Test parsing a valid CIF file."""
    cif_path = temp_cif_dir / "si.cif"
    graph = parse_cif_file(cif_path)

    assert graph is not None, "Graph should not be None for valid CIF"
    assert isinstance(graph, MaterialGraph)
    assert len(graph.node_features) == 8  # 8 Si atoms
    assert graph.node_features.shape[1] == len(NODE_FEATURES)
    assert graph.edge_indices.shape[0] == 2  # Source, Target
    # Silicon diamond structure has bonds
    assert graph.edge_indices.shape[1] > 0

def test_parse_empty_cif():
    """Test parsing an empty or invalid CIF file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cif', delete=False) as f:
        f.write("")
        f.flush()
        temp_path = Path(f.name)

    try:
        graph = parse_cif_file(temp_path)
        assert graph is None, "Graph should be None for empty CIF"
    finally:
        os.unlink(temp_path)

def test_parse_directory(temp_cif_dir):
    """Test parsing a directory of CIF files."""
    output_path = temp_cif_dir / "summary.json"
    graphs = parse_cif_directory(temp_cif_dir, output_path)

    assert len(graphs) == 2, "Should parse 2 valid CIF files"
    assert output_path.exists(), "Summary file should be created"

    # Check summary content
    import json
    with open(output_path) as f:
        summary = json.load(f)
    assert len(summary) == 2

def test_disconnected_graph_handling(temp_cif_dir):
    """Test that parser handles structures with no bonds (disconnected)."""
    cif_path = temp_cif_dir / "disconnected.cif"
    graph = parse_cif_file(cif_path)

    # The parser should not crash
    # It might return None if no bonds found and logic rejects, or valid with 0 edges
    if graph is not None:
        assert isinstance(graph, MaterialGraph)
        assert graph.node_features.shape[0] == 2
        # Edge indices shape (2, 0) if no edges
        assert graph.edge_indices.shape[1] == 0
    else:
        # If the parser returns None for disconnected structures, that is acceptable
        # as long as it doesn't crash
        pass

def test_node_features_shape(temp_cif_dir):
    """Verify node features match expected dimensionality."""
    cif_path = temp_cif_dir / "si.cif"
    graph = parse_cif_file(cif_path)

    assert graph is not None
    assert graph.node_features.shape == (8, len(NODE_FEATURES))
    # Check that features are numeric
    assert graph.node_features.dtype in [np.float32, np.float64, np.float16]

def test_edge_indices_shape(temp_cif_dir):
    """Verify edge indices are 2xN."""
    cif_path = temp_cif_dir / "si.cif"
    graph = parse_cif_file(cif_path)

    assert graph is not None
    assert graph.edge_indices.shape[0] == 2
    # Values should be valid indices
    max_idx = graph.node_features.shape[0] - 1
    assert np.all(graph.edge_indices >= 0)
    assert np.all(graph.edge_indices <= max_idx)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])