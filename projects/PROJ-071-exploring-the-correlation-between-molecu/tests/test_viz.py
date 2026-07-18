import pytest
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

from viz import (
    load_residuals_data,
    plot_residual_histogram,
    plot_qq_plot,
    plot_residuals_vs_fitted,
    generate_residual_diagnostic_plots
)
from config import get_config

@pytest.fixture
def mock_analysis_results(tmp_path):
    """Create mock analysis results with residuals data."""
    results_dir = tmp_path / "data" / "processed"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock residuals data
    n = 100
    fitted = np.random.normal(50, 10, n)
    residuals = np.random.normal(0, 2, n)  # Normally distributed residuals
    
    results = {
        'fitted': fitted.tolist(),
        'residuals': residuals.tolist(),
        'correlations': [],
        'significant_correlations': []
    }
    
    results_file = results_dir / "analysis_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f)
    
    return str(results_file), fitted, residuals

@pytest.fixture
def mock_config(tmp_path, mock_analysis_results):
    """Create a mock configuration for testing."""
    results_file, _, _ = mock_analysis_results
    
    config = {
        'paths': {
            'analysis_results': results_file,
            'processed_dir': str(Path(results_file).parent),
            'outputs_dir': str(tmp_path / "data" / "outputs"),
            'raw_dir': str(tmp_path / "data" / "raw")
        }
    }
    
    return config

def test_plot_residual_histogram(mock_config, tmp_path):
    """Test that residual histogram plot is generated correctly."""
    # Load residuals
    df = load_residuals_data(mock_config)
    residuals = df['residuals'].values
    
    # Define output path
    output_path = tmp_path / "test_residuals_hist.png"
    
    # Generate plot
    plot_residual_histogram(residuals, output_path)
    
    # Verify file exists and has content
    assert output_path.exists(), "Residual histogram plot file not created"
    assert output_path.stat().st_size > 0, "Residual histogram plot file is empty"
    
    # Clean up
    plt.close('all')

def test_plot_qq_plot(mock_config, tmp_path):
    """Test that Q-Q plot is generated correctly."""
    # Load residuals
    df = load_residuals_data(mock_config)
    residuals = df['residuals'].values
    
    # Define output path
    output_path = tmp_path / "test_qq_plot.png"
    
    # Generate plot
    plot_qq_plot(residuals, output_path)
    
    # Verify file exists and has content
    assert output_path.exists(), "Q-Q plot file not created"
    assert output_path.stat().st_size > 0, "Q-Q plot file is empty"
    
    # Clean up
    plt.close('all')

def test_plot_residuals_vs_fitted(mock_config, tmp_path):
    """Test that residuals vs fitted plot is generated correctly."""
    # Load data
    df = load_residuals_data(mock_config)
    fitted = df['fitted'].values
    residuals = df['residuals'].values
    
    # Define output path
    output_path = tmp_path / "test_residuals_vs_fitted.png"
    
    # Generate plot
    plot_residuals_vs_fitted(fitted, residuals, output_path)
    
    # Verify file exists and has content
    assert output_path.exists(), "Residuals vs fitted plot file not created"
    assert output_path.stat().st_size > 0, "Residuals vs fitted plot file is empty"
    
    # Clean up
    plt.close('all')

def test_generate_residual_diagnostic_plots(mock_config, tmp_path):
    """Test the full diagnostic plot generation pipeline."""
    # Create outputs directory in config
    outputs_dir = Path(mock_config['paths']['outputs_dir'])
    outputs_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate plots
    residuals_path, qq_path = generate_residual_diagnostic_plots(mock_config)
    
    # Verify both files exist and have content
    assert residuals_path.exists(), "Residuals plot file not created"
    assert residuals_path.stat().st_size > 0, "Residuals plot file is empty"
    
    assert qq_path.exists(), "Q-Q plot file not created"
    assert qq_path.stat().st_size > 0, "Q-Q plot file is empty"
    
    # Verify expected filenames
    assert 'residuals.png' in str(residuals_path)
    assert 'qq_plot.png' in str(qq_path)
    
    # Clean up
    plt.close('all')

def test_load_residuals_data_with_mock(mock_config):
    """Test that residuals data is loaded correctly from mock results."""
    df = load_residuals_data(mock_config)
    
    assert 'fitted' in df.columns
    assert 'residuals' in df.columns
    assert len(df) > 0
    assert not df['fitted'].isna().any()
    assert not df['residuals'].isna().any()
    
    # Check that data types are numeric
    assert pd.api.types.is_numeric_dtype(df['fitted'])
    assert pd.api.types.is_numeric_dtype(df['residuals'])