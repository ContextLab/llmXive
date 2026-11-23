import pytest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tempfile
from pathlib import Path
from src.viz import generate_boxplot_by_quartile, generate_scatterplot_with_regression

@pytest.fixture
def sample_data():
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        'sample_id': range(n),
        'sleep_efficiency': np.random.uniform(0.4, 0.95, n),
        'shannon_index': np.random.uniform(2.0, 5.0, n),
        'simpson_index': np.random.uniform(0.7, 0.95, n)
    })

def test_scatterplot_generation(sample_data, tmp_path):
    """
    Test that a scatterplot with regression line is generated and saved.
    """
    output_path = tmp_path / "test_scatter.png"
    generate_scatterplot_with_regression(
        df=sample_data,
        x_col='sleep_efficiency',
        y_col='shannon_index',
        output_path=output_path,
        title="Test Plot"
    )

    assert output_path.exists(), "Output plot file was not created."
    assert output_path.stat().st_size > 0, "Output plot file is empty."

    plt.close('all')

def test_boxplot_generation(sample_data, tmp_path):
    """
    Test that a boxplot by quartile is generated and saved.
    """
    output_path = tmp_path / "test_boxplot.png"
    generate_boxplot_by_quartile(
        df=sample_data,
        diversity_col='shannon_index',
        sleep_col='sleep_efficiency',
        output_path=output_path,
        plot_title="Test Boxplot"
    )

    assert output_path.exists(), "Output boxplot file was not created."
    assert output_path.stat().st_size > 0, "Output boxplot file is empty."

    plt.close('all')

def test_boxplot_missing_column(sample_data, tmp_path):
    """
    Test that ValueError is raised if a column is missing.
    """
    output_path = tmp_path / "test_fail.png"
    with pytest.raises(ValueError):
        generate_boxplot_by_quartile(
            df=sample_data,
            diversity_col='nonexistent_col',
            sleep_col='sleep_efficiency',
            output_path=output_path
        )

def test_scatterplot_missing_column(sample_data, tmp_path):
    """
    Test that ValueError is raised if a column is missing.
    """
    output_path = tmp_path / "test_fail.png"
    with pytest.raises(ValueError):
        generate_scatterplot_with_regression(
            df=sample_data,
            x_col='sleep_efficiency',
            y_col='nonexistent_col',
            output_path=output_path
        )
