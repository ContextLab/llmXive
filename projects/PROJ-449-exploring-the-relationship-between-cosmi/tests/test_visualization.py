"""
Tests for the visualization module (T022).

Note: These tests verify the structure and logic of the plotting functions.
They do not require the actual data file to exist if we mock the input,
but the main() function test will expect the real file path.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt

# Add code path to sys.path to import analysis modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.analysis.visualization import (
    load_correlation_results, 
    plot_heatmap, 
    plot_lag_scan, 
    generate_all_plots
)

@pytest.fixture
def mock_data():
    """Generate a mock DataFrame mimicking T020 output."""
    data = {
        'metric_type': ['He/p'] * 24 + ['He_flux'] * 24,
        'rigidity_bin': ['1.0'] * 12 + ['2.0'] * 12 + ['1.0'] * 12 + ['2.0'] * 12,
        'lag_months': list(range(-12, 13, 2)) * 4,
        'correlation': np.random.uniform(-1, 1, 48),
        'p_value': np.random.uniform(0.0, 0.1, 48)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_file(tmp_path, mock_data):
    """Create a temporary CSV file with mock data."""
    csv_path = tmp_path / "correlation_results.csv"
    mock_data.to_csv(csv_path, index=False)
    return csv_path

def test_load_correlation_results_missing_file():
    """Test that FileNotFoundError is raised if input file is missing."""
    with pytest.raises(FileNotFoundError):
        # Use a path that definitely doesn't exist
        with patch('code.analysis.visualization.INPUT_FILE', Path('/nonexistent/path.csv')):
            load_correlation_results()

def test_load_correlation_results_success(temp_csv_file, mock_data):
    """Test successful loading of correlation results."""
    # Patch the global INPUT_FILE variable
    with patch('code.analysis.visualization.INPUT_FILE', temp_csv_file):
        df = load_correlation_results()
        assert len(df) == len(mock_data)
        assert 'metric_type' in df.columns
        assert 'correlation' in df.columns
        assert df['correlation'].dtype in [np.float64, np.float32]

def test_plot_heatmap(mock_data, tmp_path):
    """Test heatmap generation."""
    output_path = tmp_path / "test_heatmap.png"
    plot_heatmap(mock_data, 'He/p', output_path, "Test Heatmap")
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_plot_lag_scan(mock_data, tmp_path):
    """Test lag scan plot generation."""
    output_path = tmp_path / "test_lag_scan.png"
    plot_lag_scan(mock_data, 'He/p', output_path, "Test Lag Scan")
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_generate_all_plots_with_mock(mock_data, tmp_path):
    """Test the full pipeline with mocked data and file paths."""
    # Create a temp CSV
    csv_path = tmp_path / "correlation_results.csv"
    mock_data.to_csv(csv_path, index=False)
    
    # Mock the global variables
    with patch('code.analysis.visualization.INPUT_FILE', csv_path):
        with patch('code.analysis.visualization.FIGURES_DIR', tmp_path / "figs"):
            generate_all_plots(mock_data)
            
            # Check that expected files were created
            fig_dir = tmp_path / "figs"
            assert fig_dir.exists()
            assert (fig_dir / "correlation_heatmap_ratios.png").exists()
            # Note: He_flux heatmap might be named differently based on metric_type logic
            # but the function should create at least the ratio heatmap.
            assert (fig_dir / "lag_scan_he_p.png").exists()

def test_plot_empty_metric(mock_data, tmp_path):
    """Test behavior when metric_type is not found."""
    output_path = tmp_path / "empty_plot.png"
    # This should log a warning and not crash
    plot_heatmap(mock_data, 'NonExistentMetric', output_path, "Empty Test")
    # File might not be created if data is empty, but no exception should be raised
    # (depending on implementation, we might create an empty figure or skip)
    # In our implementation, we return early, so file might not exist.
    # The test passes if no exception is raised.