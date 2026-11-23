"""
Unit tests for the visualization module (T022a).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Mock the config to use temporary directories
from unittest.mock import patch, MagicMock

from code.data import visualize


@pytest.fixture
def sample_data():
    """Generate a sample DataFrame for testing."""
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        'smiles': ['CCO' for _ in range(n)],
        'bond_variance': np.random.normal(0.5, 0.1, n),
        'angle_variance': np.random.normal(0.8, 0.2, n),
        'dihedral_variance': np.random.normal(1.2, 0.3, n),
        'logPapp': np.random.normal(-5.0, 1.0, n),
        'logP': np.random.normal(2.0, 0.5, n),
        'MW': np.random.normal(300.0, 50.0, n),
        'PSA': np.random.normal(60.0, 15.0, n)
    })


@pytest.fixture
def mock_paths(tmp_path):
    """Mock the project paths to use a temporary directory."""
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    figures_dir = tmp_path / "figures"
    figures_dir.mkdir(parents=True)

    # Create a dummy analysis results file
    analysis_file = data_dir / "analysis_results.csv"
    analysis_file.write_text("bond_variance,angle_variance,dihedral_variance,logPapp\n0.5,0.8,1.2,-5.0\n")

    with patch.object(visualize, 'get_data_path', return_value=data_dir.parent), \
         patch.object(visualize, 'get_figures_path', return_value=figures_dir):
        yield figures_dir


def test_load_analysis_data(mock_paths, sample_data):
    """Test that load_analysis_data reads the CSV correctly."""
    # Save sample data to the mock path
    data_dir = mock_paths.parent / "data" / "processed"
    analysis_file = data_dir / "analysis_results.csv"
    sample_data.to_csv(analysis_file, index=False)

    df = visualize.load_analysis_data()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == len(sample_data)
    assert 'bond_variance' in df.columns
    assert 'logPapp' in df.columns


def test_plot_flexibility_vs_permeability(mock_paths, sample_data):
    """Test that plot_flexibility_vs_permeability generates a PNG file."""
    # Save sample data
    data_dir = mock_paths.parent / "data" / "processed"
    analysis_file = data_dir / "analysis_results.csv"
    sample_data.to_csv(analysis_file, index=False)

    output_file = "test_plot.png"
    output_path = visualize.plot_flexibility_vs_permeability(
        df=sample_data,
        x_col="bond_variance",
        y_col="logPapp",
        output_filename=output_file
    )

    assert output_path.exists()
    assert output_path.suffix == ".png"
    # Check file size is reasonable (non-empty)
    assert output_path.stat().st_size > 1000


def test_plot_with_nan_values(mock_paths):
    """Test that the plot function handles NaN values correctly."""
    df = pd.DataFrame({
        'bond_variance': [0.5, np.nan, 0.6, 0.7],
        'logPapp': [-5.0, -4.5, np.nan, -5.2]
    })

    output_file = "test_nan_plot.png"
    output_path = visualize.plot_flexibility_vs_permeability(
        df=df,
        x_col="bond_variance",
        y_col="logPapp",
        output_filename=output_file
    )

    assert output_path.exists()
    # Should plot only the valid rows (2 rows)
    # The function should not crash


def test_plot_insufficient_data(mock_paths):
    """Test that the plot function handles insufficient data gracefully."""
    df = pd.DataFrame({
        'bond_variance': [0.5],
        'logPapp': [-5.0]
    })

    output_file = "test_insufficient.png"
    output_path = visualize.plot_flexibility_vs_permeability(
        df=df,
        x_col="bond_variance",
        y_col="logPapp",
        output_filename=output_file
    )

    assert output_path.exists()
    # Should still create a file, even if empty or with a warning message


def test_generate_all_flexibility_plots(mock_paths, sample_data):
    """Test that generate_all_flexibility_plots creates all three plots."""
    data_dir = mock_paths.parent / "data" / "processed"
    analysis_file = data_dir / "analysis_results.csv"
    sample_data.to_csv(analysis_file, index=False)

    results = visualize.generate_all_flexibility_plots(sample_data)

    expected_keys = ["bond_variance", "angle_variance", "dihedral_variance"]
    for key in expected_keys:
        assert key in results
        assert results[key] is not None
        assert results[key].exists()
        assert results[key].suffix == ".png"


def test_invalid_column_name(mock_paths, sample_data):
    """Test that an error is raised for invalid column names."""
    with pytest.raises(ValueError, match="Column 'invalid_col' not found"):
        visualize.plot_flexibility_vs_permeability(
            df=sample_data,
            x_col="invalid_col",
            y_col="logPapp",
            output_filename="test.png"
        )