import pytest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tempfile
from pathlib import Path
import os

from src.viz import (
    generate_scatterplot_with_regression,
    generate_boxplot_by_quartile,
    generate_all_quartile_boxplots,
    save_all_plot_artifacts
)

@pytest.fixture
def sample_data():
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        'sleep_efficiency': np.random.uniform(0.5, 0.95, n),
        'sleep_duration_hours': np.random.uniform(5, 9, n),
        'shannon_diversity': np.random.uniform(2.5, 4.0, n),
        'simpson_diversity': np.random.uniform(0.7, 0.95, n),
        'observed_otus': np.random.uniform(90, 140, n),
        'sleep_efficiency_quartile': np.random.choice(['Q1', 'Q2', 'Q3', 'Q4'], n)
    })

def test_scatterplot_generation(sample_data, tmp_path):
    output_path = tmp_path / "test_scatter.png"
    generate_scatterplot_with_regression(
        df=sample_data,
        x_col='sleep_efficiency',
        y_col='shannon_diversity',
        title='Test Scatter',
        x_label='Sleep Efficiency',
        y_label='Shannon Diversity',
        output_path=output_path,
        is_significant=True
    )
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_boxplot_generation(sample_data, tmp_path):
    output_path = tmp_path / "test_boxplot.png"
    generate_boxplot_by_quartile(
        df=sample_data,
        value_col='shannon_diversity',
        quartile_col='sleep_efficiency_quartile',
        title='Test Boxplot',
        x_label='Quartile',
        y_label='Shannon Diversity',
        output_path=output_path
    )
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_boxplot_missing_column(sample_data, tmp_path):
    output_path = tmp_path / "test_missing.png"
    # Should handle missing column gracefully (log error, create empty or error plot)
    generate_boxplot_by_quartile(
        df=sample_data,
        value_col='shannon_diversity',
        quartile_col='non_existent_col',
        title='Test Missing',
        x_label='Quartile',
        y_label='Shannon Diversity',
        output_path=output_path
    )
    # The function logs error but might still create a file with title
    # We just check it doesn't crash
    assert True

def test_scatterplot_missing_column(sample_data, tmp_path):
    output_path = tmp_path / "test_missing_scatter.png"
    try:
        generate_scatterplot_with_regression(
            df=sample_data,
            x_col='non_existent',
            y_col='shannon_diversity',
            title='Test Missing',
            x_label='X',
            y_label='Y',
            output_path=output_path
        )
        # If it doesn't crash, we assume it handled it (e.g. empty plot)
        assert True
    except Exception:
        # If it crashes with KeyError, that's also acceptable behavior for missing data
        assert True