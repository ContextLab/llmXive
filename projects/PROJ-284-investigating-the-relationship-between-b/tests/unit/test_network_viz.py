import os
import tempfile
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from viz.network import (
    load_schaefer_mapping,
    get_significant_edges,
    generate_network_diagram,
    main
)

@pytest.fixture
def temp_atlas_file(tmp_path):
    """Create a temporary Schaefer atlas CSV file."""
    atlas_path = tmp_path / "schaefer_400_7networks.csv"
    # Create a small dummy atlas
    data = {
        'index': range(10),
        'network': ['Visual'] * 2 + ['SomatoMotor'] * 2 + ['DorsalAttn'] * 2 + ['Salience'] * 2 + ['Default'] * 2
    }
    df = pd.DataFrame(data)
    df.to_csv(atlas_path, index=False)
    return atlas_path

@pytest.fixture
def dummy_connectivity_matrix():
    """Create a dummy 10x10 connectivity matrix."""
    np.random.seed(42)
    matrix = np.random.randn(10, 10) * 0.5
    np.fill_diagonal(matrix, 0)
    return matrix

def test_load_schaefer_mapping(temp_atlas_file):
    """Test that the atlas mapping is loaded correctly."""
    mapping = load_schaefer_mapping(temp_atlas_file)
    assert len(mapping) == 10
    assert mapping[0] == 'Visual'
    assert mapping[5] == 'DorsalAttn'

def test_get_significant_edges(dummy_connectivity_matrix):
    """Test identification of significant edges."""
    edges = get_significant_edges(
        pd.DataFrame(), 
        dummy_connectivity_matrix, 
        threshold=0.05
    )
    # We expect 5% of 100 edges = 5 edges
    assert len(edges) == 5
    for u, v, strength, is_sig in edges:
        assert u != v
        assert is_sig is True

def test_generate_network_diagram(temp_atlas_file, dummy_connectivity_matrix, tmp_path):
    """Test that the network diagram is generated and saved."""
    output_path = tmp_path / "test_network.png"
    mapping = load_schaefer_mapping(temp_atlas_file)
    edges = get_significant_edges(pd.DataFrame(), dummy_connectivity_matrix, 0.05)
    
    generate_network_diagram(dummy_connectivity_matrix, mapping, edges, output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_main_with_synthetic_data(tmp_path, monkeypatch):
    """Test the main function with synthetic data."""
    # Patch paths to use tmp_path
    import viz.network as network_module
    original_output_dir = network_module.OUTPUT_DIR
    original_atlas_path = network_module.ATLAS_PATH
    original_conn_matrix_path = network_module.conn_matrix_path if hasattr(network_module, 'conn_matrix_path') else None
    
    # We can't easily patch the module-level constants without redefining them,
    # so we'll just ensure main doesn't crash when run in a temp directory context
    # by creating the necessary files.
    
    # Create a dummy atlas
    atlas_path = tmp_path / "schaefer_400_7networks.csv"
    pd.DataFrame({'index': range(10), 'network': ['Net'] * 10}).to_csv(atlas_path, index=False)
    
    # Create a dummy connectivity matrix
    conn_path = tmp_path / "average_connectivity_matrix.npy"
    np.save(conn_path, np.random.randn(10, 10) * 0.5)
    
    # Set output dir
    output_dir = tmp_path / "figures"
    output_dir.mkdir()
    
    # Temporarily patch the module
    network_module.OUTPUT_DIR = output_dir
    network_module.ATLAS_PATH = atlas_path
    # We can't easily patch conn_matrix_path if it's not a module variable, 
    # but main() checks for the file existence, so we created it.
    
    try:
        main()
        # Check that a plot was generated
        plot_path = output_dir / "network_significant_edges.png"
        assert plot_path.exists()
    finally:
        # Restore
        network_module.OUTPUT_DIR = original_output_dir
        network_module.ATLAS_PATH = original_atlas_path