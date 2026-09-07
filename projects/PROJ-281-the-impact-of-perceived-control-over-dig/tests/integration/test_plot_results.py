import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
from unittest.mock import patch, MagicMock
import matplotlib.pyplot as plt

from code.viz.plot_results import (
    load_analysis_data,
    calculate_regression_line,
    generate_scatter_plot,
    run_visualization_pipeline
)
from code.config import CONFIG

@pytest.fixture
def sample_analysis_data():
    """Create sample analysis data for testing."""
    np.random.seed(42)
    n_samples = 100
    
    # Create synthetic data with a known negative correlation
    control_proxy = np.random.normal(0.5, 0.2, n_samples)
    anxiety_score = 1.0 - control_proxy * 0.8 + np.random.normal(0, 0.1, n_samples)
    
    df = pd.DataFrame({
        'post_id': range(n_samples),
        'control_proxy': control_proxy,
        'anxiety_score': np.clip(anxiety_score, 0, 1)
    })
    
    return df

@pytest.fixture
def mock_config(tmp_path):
    """Mock CONFIG with temporary output directory."""
    with patch.object(CONFIG, 'OUTPUT_DIR', tmp_path):
        yield CONFIG

@pytest.fixture
def final_analysis_csv(sample_analysis_data, mock_config):
    """Create the final_analysis.csv file."""
    output_path = mock_config.OUTPUT_DIR / "final_analysis.csv"
    sample_analysis_data.to_csv(output_path, index=False)
    return output_path

def test_load_analysis_data_success(final_analysis_csv, mock_config):
    """Test successful loading of analysis data."""
    df = load_analysis_data()
    
    assert len(df) > 0
    assert 'control_proxy' in df.columns
    assert 'anxiety_score' in df.columns
    assert len(df) == 100

def test_load_analysis_data_file_not_found(mock_config):
    """Test error handling when file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_analysis_data()

def test_load_analysis_data_missing_columns(mock_config, tmp_path):
    """Test error handling when required columns are missing."""
    output_path = tmp_path / "final_analysis.csv"
    pd.DataFrame({'wrong_col': [1, 2, 3]}).to_csv(output_path, index=False)
    
    with patch.object(CONFIG, 'OUTPUT_DIR', tmp_path):
        with pytest.raises(ValueError, match="Missing required columns"):
            load_analysis_data()

def test_calculate_regression_line():
    """Test regression line calculation."""
    x = np.array([1, 2, 3, 4, 5])
    y = np.array([2, 4, 5, 4, 5])
    
    x_sorted, y_reg = calculate_regression_line(x, y)
    
    # Check that x is sorted
    assert np.all(x_sorted[:-1] <= x_sorted[1:])
    assert len(x_sorted) == len(x)
    assert len(y_reg) == len(y)
    
    # Check that regression line is linear
    assert np.allclose(y_reg[1:] - y_reg[:-1], np.diff(y_reg)[0])

def test_generate_scatter_plot(sample_analysis_data):
    """Test scatter plot generation."""
    fig, ax = generate_scatter_plot(sample_analysis_data)
    
    assert fig is not None
    assert ax is not None
    assert isinstance(fig, plt.Figure)
    assert isinstance(ax, plt.Axes)
    
    # Check figure size (8x6 inches)
    assert fig.get_figwidth() == 8
    assert fig.get_figheight() == 6
    
    # Check that plot has expected elements
    assert len(ax.collections) > 0  # Scatter points
    assert len(ax.lines) > 0  # Regression line
    assert ax.get_xlabel() != ""
    assert ax.get_ylabel() != ""
    assert ax.get_title() != ""
    
    plt.close(fig)

def test_run_visualization_pipeline(final_analysis_csv, mock_config):
    """Test complete visualization pipeline."""
    fig, ax = run_visualization_pipeline()
    
    assert fig is not None
    assert ax is not None
    assert isinstance(fig, plt.Figure)
    assert isinstance(ax, plt.Axes)
    
    plt.close(fig)

def test_visualization_with_real_data_structure(final_analysis_csv, mock_config):
    """Test that visualization handles realistic data distribution."""
    # Run pipeline
    fig, ax = run_visualization_pipeline()
    
    # Verify data was plotted
    scatter = ax.collections[0]
    offsets = scatter.get_offsets()
    
    assert len(offsets) > 0
    assert offsets.shape[1] == 2  # x, y coordinates
    
    # Verify regression line exists
    assert len(ax.lines) >= 1
    
    plt.close(fig)
