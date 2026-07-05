"""
Unit tests for scatter plot generation functionality.

Tests for Task T031: Implement scatter plot generation in code/viz/plots.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing
import matplotlib.pyplot as plt

from viz.plots import create_scatter_plot, load_processed_data, generate_scatter_plot_report


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n = 1000
    data = {
        'csa_index': np.random.normal(0.5, 0.2, n),
        'food_security_score': np.random.normal(0.6, 0.15, n),
        'country': np.random.choice(['Kenya', 'India', 'Vietnam'], n),
        'region': np.random.choice(['North', 'South', 'East', 'West'], n)
    }
    
    # Add some correlation
    data['food_security_score'] = (
        0.3 * data['csa_index'] + 
        np.random.normal(0.5, 0.1, n)
    )
    
    # Add some missing values
    mask = np.random.random(n) < 0.05
    data['csa_index'][mask] = np.nan
    
    return pd.DataFrame(data)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_create_scatter_plot_basic(sample_data, temp_output_dir):
    """Test basic scatter plot creation."""
    output_path = temp_output_dir / "test_scatter.png"
    
    fig = create_scatter_plot(
        df=sample_data,
        x_col='csa_index',
        y_col='food_security_score',
        output_path=output_path
    )
    
    # Verify file was created
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    
    # Verify figure object
    assert fig is not None
    assert len(fig.axes) == 1
    
    plt.close(fig)

def test_create_scatter_plot_with_hue(sample_data, temp_output_dir):
    """Test scatter plot with hue grouping by country."""
    output_path = temp_output_dir / "test_scatter_hue.png"
    
    fig = create_scatter_plot(
        df=sample_data,
        x_col='csa_index',
        y_col='food_security_score',
        hue_col='country',
        output_path=output_path
    )
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    
    # Check that legend exists (should have 3 countries + trend line)
    ax = fig.axes[0]
    legend = ax.get_legend()
    assert legend is not None
    
    plt.close(fig)

def test_create_scatter_plot_missing_values(sample_data, temp_output_dir):
    """Test that scatter plot handles missing values correctly."""
    # Ensure we have some NaN values
    assert sample_data['csa_index'].isna().sum() > 0
    
    output_path = temp_output_dir / "test_scatter_nan.png"
    
    fig = create_scatter_plot(
        df=sample_data,
        x_col='csa_index',
        y_col='food_security_score',
        output_path=output_path
    )
    
    # Should still create a plot with non-NaN values
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    
    plt.close(fig)

def test_create_scatter_plot_empty_dataframe(temp_output_dir):
    """Test scatter plot with empty dataframe."""
    empty_df = pd.DataFrame(columns=['csa_index', 'food_security_score'])
    output_path = temp_output_dir / "test_scatter_empty.png"
    
    fig = create_scatter_plot(
        df=empty_df,
        x_col='csa_index',
        y_col='food_security_score',
        output_path=output_path
    )
    
    # Should handle gracefully (might create empty plot or return without saving)
    # The important thing is it doesn't crash
    assert fig is not None
    plt.close(fig)

def test_generate_scatter_plot_report(sample_data, temp_output_dir):
    """Test the full report generation including statistics."""
    stats = generate_scatter_plot_report(
        df=sample_data,
        output_dir=temp_output_dir
    )
    
    # Verify stats dictionary
    assert 'n_observations' in stats
    assert 'correlation_coefficient' in stats
    assert 'x_mean' in stats
    assert 'y_mean' in stats
    assert 'plot_path' in stats
    
    # Verify values
    assert stats['n_observations'] == sample_data.dropna(subset=['csa_index', 'food_security_score']).shape[0]
    assert isinstance(stats['correlation_coefficient'], float)
    assert -1 <= stats['correlation_coefficient'] <= 1
    
    # Verify files were created
    assert Path(stats['plot_path']).exists()
    assert (temp_output_dir / "scatter_plot_stats.json").exists()

def test_load_processed_data_missing_file():
    """Test that load_processed_data raises appropriate error for missing file."""
    with pytest.raises(FileNotFoundError):
        load_processed_data(Path("/nonexistent/path/data.parquet"))

def test_load_processed_data_missing_columns(temp_output_dir):
    """Test that load_processed_data raises error for missing required columns."""
    # Create a parquet file with wrong columns
    wrong_df = pd.DataFrame({
        'wrong_col1': [1, 2, 3],
        'wrong_col2': [4, 5, 6]
    })
    test_path = temp_output_dir / "wrong_columns.parquet"
    wrong_df.to_parquet(test_path)
    
    with pytest.raises(ValueError) as exc_info:
        load_processed_data(test_path)
    
    assert "Missing required columns" in str(exc_info.value)

def test_scatter_plot_trend_line(sample_data):
    """Test that trend line is calculated correctly."""
    fig = create_scatter_plot(
        df=sample_data,
        x_col='csa_index',
        y_col='food_security_score'
    )
    
    ax = fig.axes[0]
    lines = ax.get_lines()
    
    # Should have at least one line (trend line)
    assert len(lines) >= 1
    
    plt.close(fig)