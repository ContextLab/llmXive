"""
Tests for T030: Saving plot artifacts.
"""
import pytest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tempfile
from pathlib import Path
import os
import json

from src.viz import (
    generate_scatterplot_with_regression,
    generate_boxplot_by_quartile,
    generate_all_quartile_boxplots,
    save_all_plot_artifacts
)
from src.config import load_config

@pytest.fixture
def sample_data():
    """Generate sample data for testing."""
    np.random.seed(42)
    n = 100
    data = {
        'shannon_diversity': np.random.normal(3.5, 0.5, n),
        'simpson_diversity': np.random.normal(0.8, 0.1, n),
        'observed_otus': np.random.normal(150, 20, n),
        'sleep_efficiency': np.random.uniform(50, 100, n),
        'sleep_duration_hours': np.random.uniform(5, 9, n),
        'antibiotic_use_last_3m': np.random.choice([True, False], n)
    }
    df = pd.DataFrame(data)
    # Add quartile column manually for testing
    df['sleep_efficiency_quartile'] = pd.qcut(df['sleep_efficiency'], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'], duplicates='drop')
    return df

@pytest.fixture
def sample_correlation_results(tmp_path):
    """Create a mock correlation results file."""
    results = {
        'metric': ['shannon_diversity', 'simpson_diversity'],
        'sleep_variable': ['sleep_efficiency', 'sleep_duration_hours'],
        'r': [0.45, -0.32],
        'p': [0.001, 0.04],
        'q': [0.005, 0.06],
        'is_moderate': [True, True],
        'is_meaningful': [True, False] # Only one is meaningful
    }
    df = pd.DataFrame(results)
    path = tmp_path / "correlation_results.csv"
    df.to_csv(path, index=False)
    return path

@pytest.fixture
def mock_config(tmp_path):
    """Mock config for T030."""
    config = {
        'PLOTS_DIR': str(tmp_path / "plots"),
        'CORRELATION_RESULTS_PATH': str(tmp_path / "correlation_results.csv"),
        'CLEANED_DATA_PATH': str(tmp_path / "cleaned_data.csv")
    }
    # Create dummy files
    pd.DataFrame({'col': [1]}).to_csv(tmp_path / "cleaned_data.csv", index=False)
    # We will set the correlation path via fixture
    return config

def test_scatterplot_generation(sample_data, tmp_path):
    """Test that a scatterplot is generated and saved."""
    output_path = tmp_path / "test_scatter.png"
    generate_scatterplot_with_regression(
        data=sample_data,
        x_col='sleep_efficiency',
        y_col='shannon_diversity',
        title='Test Scatter',
        output_path=output_path
    )
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_boxplot_generation(sample_data, tmp_path):
    """Test that a boxplot is generated and saved."""
    output_path = tmp_path / "test_boxplot.png"
    generate_boxplot_by_quartile(
        data=sample_data,
        value_col='shannon_diversity',
        quartile_col='sleep_efficiency_quartile',
        title='Test Boxplot',
        output_path=output_path
    )
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_boxplot_missing_column(sample_data, tmp_path):
    """Test that missing column raises ValueError."""
    output_path = tmp_path / "fail.png"
    with pytest.raises(ValueError):
        generate_boxplot_by_quartile(
            data=sample_data,
            value_col='nonexistent_col',
            quartile_col='sleep_efficiency_quartile',
            title='Test',
            output_path=output_path
        )

def test_scatterplot_missing_column(sample_data, tmp_path):
    """Test that missing column raises ValueError."""
    output_path = tmp_path / "fail.png"
    with pytest.raises(ValueError):
        generate_scatterplot_with_regression(
            data=sample_data,
            x_col='nonexistent_x',
            y_col='shannon_diversity',
            title='Test',
            output_path=output_path
        )

def test_save_all_plot_artifacts_integration(tmp_path, monkeypatch):
    """Integration test for saving all plot artifacts."""
    # Create necessary directories and files
    plots_dir = tmp_path / "plots"
    plots_dir.mkdir()
    
    # Create mock correlation results
    corr_data = {
        'metric': ['shannon_diversity'],
        'sleep_variable': ['sleep_efficiency'],
        'r': [0.45],
        'p': [0.001],
        'q': [0.005],
        'is_moderate': [True],
        'is_meaningful': [True]
    }
    corr_df = pd.DataFrame(corr_data)
    corr_path = tmp_path / "correlation_results.csv"
    corr_df.to_csv(corr_path, index=False)

    # Create mock cleaned data
    cleaned_data = {
        'shannon_diversity': [3.1, 3.5, 3.8],
        'sleep_efficiency': [60, 75, 90],
        'sleep_efficiency_quartile': ['Q1', 'Q2', 'Q3']
    }
    cleaned_df = pd.DataFrame(cleaned_data)
    cleaned_path = tmp_path / "cleaned_data.csv"
    cleaned_df.to_csv(cleaned_path, index=False)

    # Patch config
    def mock_load_config():
        return {
            'PLOTS_DIR': str(plots_dir),
            'CORRELATION_RESULTS_PATH': str(corr_path),
            'CLEANED_DATA_PATH': str(cleaned_path)
        }
    monkeypatch.setattr('src.viz.load_config', mock_load_config)

    # Run the function
    saved_paths = save_all_plot_artifacts()

    # Verify outputs
    assert len(saved_paths) > 0
    for p in saved_paths:
        assert p.exists()
        assert p.stat().st_size > 0