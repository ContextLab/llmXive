"""
Unit tests for the visualization module.
"""
import os
import json
import pickle
import tempfile
from pathlib import Path
import numpy as np
import pytest
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing
import matplotlib.pyplot as plt

from visualize import (
    load_fpca_results,
    plot_temporal_modes,
    plot_spatial_patterns,
    plot_cumulative_variance,
    generate_all_visualizations
)
from config import get_data_dir, get_artifacts_dir

@pytest.fixture
def mock_fpca_results(tmp_path):
    """Create mock fPCA results for testing."""
    # Create mock data
    n_components = 5
    n_time_points = 100
    n_lat = 20
    n_lon = 30
    
    eigenvalues = np.array([0.3, 0.25, 0.15, 0.1, 0.05])
    eigenfunctions = np.random.randn(n_components, n_time_points)
    
    time_grid = np.linspace(0, 100, n_time_points)
    lats = np.linspace(-90, 90, n_lat)
    lons = np.linspace(-180, 180, n_lon)
    
    # Create spatial patterns (3D: components x lat x lon)
    spatial_patterns = np.random.randn(n_components, n_lat, n_lon)
    
    results = {
        'eigenvalues': eigenvalues,
        'eigenfunctions': eigenfunctions,
        'spatial_patterns': spatial_patterns,
        'metadata': {
            'time_grid': time_grid,
            'spatial_grid': (lons, lats),
            'time_points': np.linspace(0, 100, 10).tolist()
        }
    }
    
    # Save to temporary file
    results_path = tmp_path / "fpca_results.pkl"
    with open(results_path, 'wb') as f:
        pickle.dump(results, f)
        
    return results_path

def test_load_fpca_results(mock_fpca_results):
    """Test loading fPCA results from disk."""
    results = load_fpca_results(mock_fpca_results)
    
    assert 'eigenvalues' in results
    assert 'eigenfunctions' in results
    assert 'metadata' in results
    assert len(results['eigenvalues']) == 5
    assert results['eigenfunctions'].shape[0] == 5

def test_plot_temporal_modes(mock_fpca_results, tmp_path):
    """Test plotting temporal modes."""
    results = load_fpca_results(mock_fpca_results)
    output_path = tmp_path / "temporal_modes.png"
    
    plot_temporal_modes(
        results['eigenfunctions'],
        results['eigenvalues'],
        results['metadata']['time_grid'],
        output_path,
        n_components=3
    )
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_plot_cumulative_variance(mock_fpca_results, tmp_path):
    """Test plotting cumulative variance."""
    results = load_fpca_results(mock_fpca_results)
    output_path = tmp_path / "cumulative_variance.png"
    
    plot_cumulative_variance(results['eigenvalues'], output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_plot_spatial_patterns(mock_fpca_results, tmp_path):
    """Test plotting spatial patterns."""
    results = load_fpca_results(mock_fpca_results)
    output_dir = tmp_path / "spatial_patterns"
    output_dir.mkdir()
    
    spatial_grid = results['metadata']['spatial_grid']
    time_points = results['metadata']['time_points']
    
    plot_spatial_patterns(
        results['spatial_patterns'],
        spatial_grid,
        time_points,
        output_dir,
        n_components=2,
        time_point_indices=[0, -1]
    )
    
    # Check that files were created
    files = list(output_dir.glob("*.png"))
    assert len(files) >= 2  # At least 2 components * 2 time points

def test_generate_all_visualizations(mock_fpca_results, tmp_path):
    """Test generating all visualizations."""
    output_dir = tmp_path / "visualizations"
    
    output_paths = generate_all_visualizations(
        mock_fpca_results,
        output_dir,
        n_components=3
    )
    
    assert 'temporal_modes' in output_paths
    assert 'cumulative_variance' in output_paths
    assert 'spatial_patterns' in output_paths
    
    # Check that files exist
    assert Path(output_paths['temporal_modes']).exists()
    assert Path(output_paths['cumulative_variance']).exists()
    assert Path(output_paths['spatial_patterns']).exists()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])