"""
Unit tests for T027: Scatterplot generation with regression lines.
"""
import pytest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tempfile
from pathlib import Path
from src.viz import (
    generate_scatterplot_with_regression,
    generate_boxplot_by_quartile,
    save_all_plot_artifacts
)

@pytest.fixture
def sample_data():
    """Generate sample data for testing."""
    np.random.seed(42)
    n = 100
    data = pd.DataFrame({
        'shannon_diversity': np.random.normal(3.5, 0.5, n),
        'sleep_efficiency': np.random.normal(85, 10, n),
        'sleep_duration_hours': np.random.normal(7.5, 1.0, n)
    })
    # Add some correlation
    data['sleep_efficiency'] = data['sleep_efficiency'] + 2 * data['shannon_diversity']
    return data

@pytest.fixture
def sample_correlation_results():
    """Generate sample correlation results."""
    return pd.DataFrame({
        'diversity_index': ['shannon_diversity', 'simpson_diversity'],
        'sleep_metric': ['sleep_efficiency', 'sleep_duration_hours'],
        'r': [0.45, -0.2],
        'p': [0.001, 0.08],
        'q': [0.003, 0.12],
        'is_moderate': [True, False],
        'is_meaningful': [True, False],
        'status': ['success', 'success']
    })

def test_scatterplot_generation(sample_data, tmp_path):
    """Test that scatterplot generation creates a valid file."""
    output_path = tmp_path / "test_scatterplot.png"

    generate_scatterplot_with_regression(
        data=sample_data,
        x_col='shannon_diversity',
        y_col='sleep_efficiency',
        title='Test Scatterplot',
        x_label='Shannon Diversity',
        y_label='Sleep Efficiency',
        output_path=output_path,
        correlation_info={'r': 0.45, 'p': 0.001, 'q': 0.003}
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0

    # Verify file is a valid image by checking header
    with open(output_path, 'rb') as f:
        header = f.read(8)
        assert header[:8] == b'\x89PNG\r\n\x1a\n'

def test_scatterplot_missing_column(sample_data, tmp_path):
    """Test that missing columns raise an error."""
    output_path = tmp_path / "test_scatterplot.png"

    with pytest.raises(ValueError, match="not found in data"):
        generate_scatterplot_with_regression(
            data=sample_data,
            x_col='nonexistent_col',
            y_col='sleep_efficiency',
            title='Test',
            x_label='X',
            y_label='Y',
            output_path=output_path
        )

def test_scatterplot_empty_dataframe(tmp_path):
    """Test that empty DataFrame raises an error."""
    output_path = tmp_path / "test_scatterplot.png"
    empty_data = pd.DataFrame(columns=['x', 'y'])

    with pytest.raises(ValueError, match="DataFrame is empty"):
        generate_scatterplot_with_regression(
            data=empty_data,
            x_col='x',
            y_col='y',
            title='Test',
            x_label='X',
            y_label='Y',
            output_path=output_path
        )

def test_boxplot_generation(sample_data, tmp_path):
    """Test that boxplot generation creates a valid file."""
    output_path = tmp_path / "test_boxplot.png"

    generate_boxplot_by_quartile(
        data=sample_data,
        diversity_col='shannon_diversity',
        sleep_col='sleep_efficiency',
        title='Test Boxplot',
        x_label='Sleep Quartile',
        y_label='Shannon Diversity',
        output_path=output_path
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_boxplot_missing_column(sample_data, tmp_path):
    """Test that missing columns raise an error."""
    output_path = tmp_path / "test_boxplot.png"

    with pytest.raises(ValueError, match="not found in data"):
        generate_boxplot_by_quartile(
            data=sample_data,
            diversity_col='nonexistent_col',
            sleep_col='sleep_efficiency',
            title='Test',
            x_label='X',
            y_label='Y',
            output_path=output_path
        )

def test_save_all_plot_artifacts(sample_data, sample_correlation_results, tmp_path):
    """Test the full artifact generation pipeline."""
    saved_paths = save_all_plot_artifacts(
        correlation_results=sample_correlation_results,
        cleaned_data=sample_data,
        output_dir=tmp_path
    )

    # Should have at least one scatterplot and boxplots
    assert len(saved_paths) >= 1

    # Verify all files exist and are non-empty
    for path in saved_paths:
        assert path.exists()
        assert path.stat().st_size > 0

    # Verify file naming convention
    scatterplots = [p for p in saved_paths if 'scatterplot' in p.name]
    boxplots = [p for p in saved_paths if 'boxplot' in p.name]

    assert len(scatterplots) >= 1  # At least one meaningful correlation
    assert len(boxplots) >= 1      # At least one boxplot