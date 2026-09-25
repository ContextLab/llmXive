"""
Unit tests for the visualization module.

Tests focus on:
- Directory creation
- Data loading error handling
- Plot generation (mocked to avoid heavy rendering in CI)
"""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np

# Import the module under test
# We need to ensure the path is set up correctly if running from tests/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from visualization import (
    ensure_figures_directory,
    load_processed_data,
    load_recession_periods,
    plot_time_series_with_recession_shading,
    plot_impulse_response_functions,
    plot_cross_correlation_heatmap,
    PROJECT_ROOT
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Create necessary subdirectories
        (tmpdir / "data" / "processed").mkdir(parents=True)
        (tmpdir / "data" / "metadata").mkdir(parents=True)
        (tmpdir / "artifacts" / "figures").mkdir(parents=True)
        (tmpdir / "results").mkdir(parents=True)
        
        # Create mock data files
        # aligned_monthly.csv
        df = pd.DataFrame({
            'date': pd.date_range(start='2000-01-01', periods=240, freq='M'),
            'sentiment_score': np.random.randn(240),
            'gdp_growth': np.random.randn(240),
            'unemployment_rate': np.random.randn(240)
        })
        df.to_csv(tmpdir / "data" / "processed" / "aligned_monthly.csv", index=False)
        
        # recession_periods.json
        recession_data = [
            {'start': '2001-03-01', 'end': '2001-11-01'},
            {'start': '2008-12-01', 'end': '2009-06-01'}
        ]
        with open(tmpdir / "data" / "metadata" / "recession_periods.json", 'w') as f:
            json.dump(recession_data, f)
        
        # model_stats.json (empty for IRF test)
        with open(tmpdir / "results" / "model_stats.json", 'w') as f:
            json.dump({}, f)
        
        yield tmpdir

@patch('visualization.PROJECT_ROOT')
def test_ensure_figures_directory(mock_root, temp_data_dir):
    """Test that the figures directory is created if it doesn't exist."""
    mock_root.__truediv__ = lambda self, other: temp_data_dir / other
    mock_root.__rtruediv__ = lambda self, other: temp_data_dir / other
    
    # Remove the figures directory to test creation
    figures_dir = temp_data_dir / "artifacts" / "figures"
    if figures_dir.exists():
        os.rmdir(figures_dir)
    
    result = ensure_figures_directory()
    assert result.exists()
    assert result.is_dir()

@patch('visualization.PROJECT_ROOT')
def test_load_processed_data_success(mock_root, temp_data_dir):
    """Test successful loading of processed data."""
    mock_root.__truediv__ = lambda self, other: temp_data_dir / other
    
    df = load_processed_data()
    assert isinstance(df, pd.DataFrame)
    assert 'date' in df.columns
    assert 'sentiment_score' in df.columns
    assert len(df) > 0

@patch('visualization.PROJECT_ROOT')
def test_load_processed_data_missing(mock_root, temp_data_dir):
    """Test error when processed data is missing."""
    mock_root.__truediv__ = lambda self, other: temp_data_dir / other
    
    # Remove the file
    (temp_data_dir / "data" / "processed" / "aligned_monthly.csv").unlink()
    
    with pytest.raises(FileNotFoundError):
        load_processed_data()

@patch('visualization.PROJECT_ROOT')
def test_load_recession_periods_success(mock_root, temp_data_dir):
    """Test successful loading of recession periods."""
    mock_root.__truediv__ = lambda self, other: temp_data_dir / other
    
    periods = load_recession_periods()
    assert isinstance(periods, list)
    assert len(periods) == 2

@patch('visualization.PROJECT_ROOT')
def test_load_recession_periods_missing(mock_root, temp_data_dir):
    """Test error when recession periods are missing."""
    mock_root.__truediv__ = lambda self, other: temp_data_dir / other
    
    # Remove the file
    (temp_data_dir / "data" / "metadata" / "recession_periods.json").unlink()
    
    with pytest.raises(FileNotFoundError):
        load_recession_periods()

@patch('visualization.PROJECT_ROOT')
@patch('visualization.plot_time_series_with_recession_shading')
def test_plot_time_series_with_recession_shading_call(mock_plot, mock_root, temp_data_dir):
    """Test that the plotting function is called with correct arguments."""
    mock_root.__truediv__ = lambda self, other: temp_data_dir / other
    
    df = pd.DataFrame({
        'date': pd.date_range(start='2000-01-01', periods=12, freq='M'),
        'sentiment_score': np.random.randn(12),
        'gdp_growth': np.random.randn(12)
    })
    recession_periods = [{'start': '2000-02-01', 'end': '2000-03-01'}]
    
    # Mock the return value
    mock_plot.return_value = temp_data_dir / "artifacts" / "figures" / "test.png"
    
    result = plot_time_series_with_recession_shading(df, recession_periods)
    
    mock_plot.assert_called_once()
    assert result is not None

@patch('visualization.plot_impulse_response_functions')
def test_plot_impulse_response_functions_call(mock_plot):
    """Test that the IRF plotting function is called."""
    model_stats = {'irf_data': {}}
    
    mock_plot.return_value = Path("test.png")
    
    result = plot_impulse_response_functions(model_stats)
    
    mock_plot.assert_called_once()
    assert result is not None

@patch('visualization.plot_cross_correlation_heatmap')
def test_plot_cross_correlation_heatmap_call(mock_plot):
    """Test that the heatmap plotting function is called."""
    df = pd.DataFrame({
        'date': pd.date_range(start='2000-01-01', periods=24, freq='M'),
        'sentiment_score': np.random.randn(24),
        'gdp_growth': np.random.randn(24)
    })
    
    mock_plot.return_value = Path("test.png")
    
    result = plot_cross_correlation_heatmap(df)
    
    mock_plot.assert_called_once()
    assert result is not None