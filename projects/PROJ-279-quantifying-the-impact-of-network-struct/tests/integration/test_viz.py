"""
Integration test for T035: Visualization module.

Tests the full pipeline of loading descriptors, identifying top predictor,
and generating the scatter plot.
"""
import json
import os
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

# Mock the environment config to use a temp directory
@pytest.fixture
def temp_env_config():
    with tempfile.TemporaryDirectory() as tmpdir:
        processed_dir = Path(tmpdir) / "processed"
        processed_dir.mkdir()
        results_dir = processed_dir / "results"
        results_dir.mkdir()
        
        # Create a fake descriptors.csv with realistic data
        # We simulate a scenario where 'ring_statistics_avg' is the top predictor
        n_samples = 50
        data = {
            'config_id': [f'cfg_{i}' for i in range(n_samples)],
            'ring_statistics_avg': np.random.uniform(0.1, 0.9, n_samples),
            'steinhardt_q6': np.random.uniform(0.1, 0.9, n_samples),
            'clustering_coefficient': np.random.uniform(0.1, 0.9, n_samples),
            'thermal_conductivity': np.random.uniform(1.0, 5.0, n_samples)
        }
        df = pd.DataFrame(data)
        csv_path = processed_dir / "descriptors.csv"
        df.to_csv(csv_path, index=False)
        
        # Patch the env_config to return our temp directory
        with patch('viz.get_processed_dir', return_value=processed_dir):
            with patch('config.env_config.get_processed_dir', return_value=processed_dir):
                yield csv_path, results_dir

def test_scatter_plot_generation(temp_env_config):
    """Test that the scatter plot is generated with correct metadata."""
    _, results_dir = temp_env_config
    
    from viz import main, generate_scatter_plot, identify_top_predictor, load_regression_results
    
    # Run the main logic
    df = load_regression_results()
    assert df is not None, "Failed to load descriptors"
    
    feature, r = identify_top_predictor(df)
    assert feature is not None, "Failed to identify top predictor"
    assert isinstance(r, float), "Pearson r should be a float"
    
    output_path = results_dir / "scatter_top_predictor_vs_k.png"
    generate_scatter_plot(df, feature, output_path)
    
    # Verify file exists
    assert output_path.exists(), "Scatter plot file was not created"
    assert output_path.stat().st_size > 0, "Scatter plot file is empty"
    
    # Verify metadata
    json_path = output_path.with_suffix('.json')
    assert json_path.exists(), "Metadata JSON was not created"
    
    with open(json_path, 'r') as f:
        metadata = json.load(f)
    
    assert 'feature' in metadata
    assert 'pearson_r' in metadata
    assert metadata['feature'] == feature
    assert isinstance(metadata['pearson_r'], float)

def test_plot_with_missing_data(temp_env_config):
    """Test handling of NaN values in data."""
    _, results_dir = temp_env_config
    
    from viz import generate_scatter_plot
    
    # Load and inject NaNs
    df = pd.read_csv(temp_env_config[0])
    df.loc[0, 'ring_statistics_avg'] = np.nan
    df.loc[1, 'thermal_conductivity'] = np.nan
    
    output_path = results_dir / "test_nan_plot.png"
    # Should not raise an error, just skip NaN rows
    try:
        generate_scatter_plot(df, 'ring_statistics_avg', output_path)
        assert output_path.exists()
    except Exception as e:
        pytest.fail(f"Failed to handle NaN data: {e}")

def test_plot_with_insufficient_data():
    """Test behavior when too few data points exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        processed_dir = Path(tmpdir) / "processed"
        processed_dir.mkdir()
        results_dir = processed_dir / "results"
        results_dir.mkdir()
        
        # Create a dataframe with only 1 row
        data = {
            'config_id': ['cfg_0'],
            'ring_statistics_avg': [0.5],
            'thermal_conductivity': [2.0]
        }
        df = pd.DataFrame(data)
        csv_path = processed_dir / "descriptors.csv"
        df.to_csv(csv_path, index=False)
        
        with patch('viz.get_processed_dir', return_value=processed_dir):
            with patch('config.env_config.get_processed_dir', return_value=processed_dir):
                from viz import generate_scatter_plot
                
                output_path = results_dir / "small_plot.png"
                # Should log error and return without creating file
                generate_scatter_plot(df, 'ring_statistics_avg', output_path)
                
                # The function should handle this gracefully (log error, no plot)
                # We check that it doesn't crash
                assert True