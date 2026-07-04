"""
Unit tests for the visualization module (T022).

Tests verify that plotting functions handle data correctly and produce files.
Note: These tests use mocked data to avoid dependency on full EDA pipeline execution.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# We need to mock the config paths to point to a temp directory
# so we don't write to the real project data/figures during tests
@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = os.path.join(tmpdir, "results")
        figures_dir = os.path.join(tmpdir, "figures")
        os.makedirs(results_dir)
        os.makedirs(figures_dir)
        yield {
            "results": results_dir,
            "figures": figures_dir,
            "tmp": tmpdir
        }

@pytest.fixture
def mock_config(monkeypatch, temp_dirs):
    """Mock config.get_path to return temp directories."""
    def mock_get_path(key):
        if key == "results":
            return temp_dirs["results"]
        elif key == "figures":
            return temp_dirs["figures"]
        return temp_dirs["tmp"]
    
    monkeypatch.setattr("visualization.get_path", mock_get_path)
    return temp_dirs

@pytest.fixture
def sample_correlation_data(temp_dirs):
    """Create a sample correlation matrix CSV."""
    data = {
        'temp': [1.0, 0.8, -0.5],
        'building_density': [0.8, 1.0, -0.3],
        'tree_cover': [-0.5, -0.3, 1.0]
    }
    df = pd.DataFrame(data, index=['temp', 'building_density', 'tree_cover'])
    csv_path = os.path.join(temp_dirs["results"], "correlation_matrix.csv")
    df.to_csv(csv_path)
    return csv_path

@pytest.fixture
def sample_spatial_stats(temp_dirs):
    """Create a sample spatial stats JSON with variogram data."""
    data = {
        "moran_i": 0.45,
        "p_value": 0.001,
        "variogram": {
            "lags": [10, 20, 30, 40, 50],
            "semivariance": [0.1, 0.25, 0.45, 0.60, 0.70],
            "model": {
                "fitted_lags": [10, 20, 30, 40, 50],
                "fitted_semivariance": [0.12, 0.24, 0.44, 0.58, 0.68]
            }
        }
    }
    json_path = os.path.join(temp_dirs["results"], "spatial_stats.json")
    with open(json_path, 'w') as f:
        json.dump(data, f)
    return json_path

def test_load_correlation_matrix(mock_config, sample_correlation_data):
    """Test loading correlation matrix from CSV."""
    from visualization import load_correlation_matrix
    
    df = load_correlation_matrix()
    assert isinstance(df, pd.DataFrame)
    assert 'temp' in df.columns
    assert df.loc['temp', 'building_density'] == pytest.approx(0.8)

def test_load_spatial_stats(mock_config, sample_spatial_stats):
    """Test loading spatial stats from JSON."""
    from visualization import load_spatial_stats
    
    stats = load_spatial_stats()
    assert isinstance(stats, dict)
    assert 'variogram' in stats
    assert len(stats['variogram']['lags']) == 5

def test_plot_correlation_heatmap(mock_config, sample_correlation_data, sample_spatial_stats):
    """Test that correlation heatmap is generated and saved."""
    from visualization import plot_correlation_heatmap
    
    output_file = plot_correlation_heatmap()
    
    assert os.path.exists(output_file)
    assert output_file.endswith('.png')
    # Check file size is non-zero
    assert os.path.getsize(output_file) > 0

def test_plot_variogram(mock_config, sample_correlation_data, sample_spatial_stats):
    """Test that variogram plot is generated and saved."""
    from visualization import plot_variogram
    
    output_file = plot_variogram()
    
    assert os.path.exists(output_file)
    assert output_file.endswith('.png')
    assert os.path.getsize(output_file) > 0

def test_plot_variogram_missing_data(mock_config, temp_dirs):
    """Test that variogram plot fails gracefully if data is missing."""
    from visualization import plot_variogram
    
    # Create an empty spatial stats file
    json_path = os.path.join(temp_dirs["results"], "spatial_stats.json")
    with open(json_path, 'w') as f:
        json.dump({"moran_i": 0.45}, f)
    
    with pytest.raises(ValueError, match="Variogram data missing"):
        plot_variogram()

def test_plot_combined_eda(mock_config, sample_correlation_data, sample_spatial_stats):
    """Test combined EDA summary generation."""
    from visualization import plot_combined_eda
    
    output_file = plot_combined_eda()
    
    assert os.path.exists(output_file)
    assert output_file.endswith('.png')
    assert os.path.getsize(output_file) > 0
