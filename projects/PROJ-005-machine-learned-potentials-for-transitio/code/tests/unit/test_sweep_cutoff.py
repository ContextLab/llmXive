"""
Unit tests for T017: Cutoff Sensitivity Analysis.
"""

import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from src.data.sweep_cutoff import (
    analyze_cutoff,
    run_sensitivity_analysis,
    save_results,
    get_project_root
)

@pytest.fixture
def mock_graph_data():
    """
    Creates a mock DataFrame with graph data suitable for testing.
    """
    # Create 2 mock graphs
    # Graph 1: 4 atoms in a square (approx 2.0A apart)
    coords_1 = [
        [0.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],
        [2.0, 2.0, 0.0],
        [0.0, 2.0, 0.0]
    ]
    atoms_1 = [6, 6, 6, 6] # Carbon

    # Graph 2: 3 atoms in a triangle (approx 1.5A apart)
    coords_2 = [
        [0.0, 0.0, 0.0],
        [1.5, 0.0, 0.0],
        [0.75, 1.3, 0.0]
    ]
    atoms_2 = [1, 1, 1] # Hydrogen

    data = {
        'coordinates': [coords_1, coords_2],
        'atomic_numbers': [atoms_1, atoms_2],
        'reaction_id': ['r1', 'r2']
    }
    return pd.DataFrame(data)

def test_analyze_cutoff_small(mock_graph_data):
    """Test analysis with a small cutoff (1.0A) - should result in 0 edges."""
    result = analyze_cutoff(mock_graph_data, cutoff=1.0)
    
    assert result['total_edges'] == 0
    assert result['avg_density'] == 0.0
    assert result['cutoff'] == 1.0
    assert result['num_graphs_analyzed'] == 2

def test_analyze_cutoff_medium(mock_graph_data):
    """Test analysis with a medium cutoff (2.5A) - should connect neighbors in Graph 1."""
    result = analyze_cutoff(mock_graph_data, cutoff=2.5)
    
    # Graph 1: 4 edges (square)
    # Graph 2: 3 edges (triangle, all < 2.5)
    # Total expected edges: 4 + 3 = 7
    # Note: distance between (0,0) and (2,2) is sqrt(8) ~ 2.82 > 2.5, so no diagonal
    assert result['total_edges'] == 7
    assert result['avg_density'] > 0.0

def test_analyze_cutoff_large(mock_graph_data):
    """Test analysis with a large cutoff (5.0A) - should connect everything."""
    result = analyze_cutoff(mock_graph_data, cutoff=5.0)
    
    # Graph 1: 6 edges (complete graph K4)
    # Graph 2: 3 edges (complete graph K3)
    # Total: 9 edges
    assert result['total_edges'] == 9

def test_run_sensitivity_analysis(mock_graph_data):
    """Test the full sensitivity analysis pipeline."""
    cutoffs = [1.0, 2.5, 5.0]
    results = run_sensitivity_analysis(mock_graph_data, cutoffs=cutoffs)
    
    assert len(results) == 3
    
    # Check structure of results
    for res in results:
        assert 'cutoff' in res
        assert 'total_edges' in res
        assert 'avg_density' in res
        assert 'total_nodes' in res

def test_save_results():
    """Test saving results to a temporary file."""
    results = [
        {'cutoff': 2.5, 'total_edges': 10, 'avg_density': 0.5},
        {'cutoff': 3.5, 'total_edges': 12, 'avg_density': 0.6}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_sensitivity.json"
        saved_path = save_results(results, output_path)
        
        assert saved_path.exists()
        
        with open(saved_path, 'r') as f:
            loaded = json.load(f)
            
        assert loaded == results

def test_coordination_number_calculation(mock_graph_data):
    """Verify coordination numbers are calculated correctly."""
    # With cutoff 2.5, Graph 1 (square) should have degree 2 for all nodes
    # Graph 2 (triangle) should have degree 2 for all nodes
    result = analyze_cutoff(mock_graph_data, cutoff=2.5)
    
    # Total nodes = 4 + 3 = 7
    # Total edges = 7
    # Sum of degrees = 2 * edges = 14
    # Avg coord = 14 / 7 = 2.0
    assert abs(result['avg_coordination_number'] - 2.0) < 1e-5

def test_outlier_detection(mock_graph_data):
    """Test that outliers (coord > 6) are detected if present."""
    # Create a graph with a central atom connected to many neighbors
    # Central at (0,0,0), neighbors at (1,0,0), (0,1,0), (0,0,1), (-1,0,0), (0,-1,0), (0,0,-1)
    # 6 neighbors -> coord 6 (not outlier)
    # Add one more at (1.5, 0, 0) -> coord 7 (outlier)
    
    coords = [
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [-1.0, 0.0, 0.0],
        [0.0, -1.0, 0.0],
        [0.0, 0.0, -1.0],
        [1.5, 0.0, 0.0]
    ]
    atoms = [6] * 8
    
    df = pd.DataFrame({
        'coordinates': [coords],
        'atomic_numbers': [atoms]
    })
    
    # Cutoff 2.0 should connect the 7th neighbor (1.5)
    result = analyze_cutoff(df, cutoff=2.0)
    
    # The central atom has 7 neighbors within 2.0A
    # So outlier_count should be at least 1
    assert result['outlier_count'] >= 1