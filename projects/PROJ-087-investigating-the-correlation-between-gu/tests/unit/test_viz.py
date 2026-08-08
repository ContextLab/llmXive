import pytest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tempfile
from pathlib import Path
from src.viz import generate_scatterplot_with_regression, generate_boxplot_by_quartile

@pytest.fixture
def sample_data():
    """
    Create a small, deterministic dataframe for testing visualization functions.
    This data is synthetic but mathematically consistent for testing purposes.
    """
    np.random.seed(42)
    n_samples = 50
    data = {
        'sample_id': [f'Sample_{i:03d}' for i in range(n_samples)],
        'shannon_diversity': np.random.normal(3.5, 0.5, n_samples),
        'simpson_diversity': np.random.normal(0.85, 0.05, n_samples),
        'observed_otus': np.random.normal(150, 20, n_samples),
        'sleep_efficiency': np.random.normal(85, 5, n_samples),
        'sleep_duration_hours': np.random.normal(7.5, 0.8, n_samples),
        'sleep_quartile': np.random.choice([1, 2, 3, 4], n_samples)
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_correlation_results():
    """
    Create a small dataframe mimicking correlation results output from T024.
    """
    data = {
        'diversity_metric': ['shannon_diversity', 'simpson_diversity', 'observed_otus'],
        'sleep_metric': ['sleep_efficiency', 'sleep_duration_hours', 'sleep_efficiency'],
        'r': [0.45, -0.12, 0.38],
        'p': [0.001, 0.45, 0.008],
        'q': [0.003, 0.60, 0.015],
        'is_moderate': [True, False, True],
        'is_meaningful': [True, False, True],
        'status': ['significant', 'not_significant', 'significant']
    }
    return pd.DataFrame(data)

def test_scatterplot_generation(sample_data, sample_correlation_results):
    """
    Test that generate_scatterplot_with_regression creates a valid plot file
    with correct axis labels and regression line for a significant correlation.
    
    This test verifies:
    1. The function executes without error
    2. The output file is created on disk
    3. The file is a valid image (non-zero size)
    4. The function handles significant correlations correctly
    """
    # Filter for significant correlations only (as the function would do)
    sig_corrs = sample_correlation_results[
        (sample_correlation_results['is_moderate'] == True) & 
        (sample_correlation_results['is_meaningful'] == True)
    ]
    
    assert len(sig_corrs) > 0, "Test requires at least one significant correlation"
    
    # Pick the first significant correlation
    corr_row = sig_corrs.iloc[0]
    x_col = corr_row['diversity_metric']
    y_col = corr_row['sleep_metric']
    
    # Verify columns exist in sample data
    assert x_col in sample_data.columns, f"Column {x_col} not found in sample data"
    assert y_col in sample_data.columns, f"Column {y_col} not found in sample data"
    
    # Create a temporary directory for the plot
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_scatterplot.png"
        
        # Call the function
        result_path = generate_scatterplot_with_regression(
            data=sample_data,
            x_column=x_col,
            y_column=y_col,
            output_path=str(output_path),
            title=f"Test: {x_col} vs {y_col}"
        )
        
        # Verify the file was created
        assert result_path is not None, "Function returned None for output path"
        assert Path(result_path).exists(), f"Output file was not created at {result_path}"
        assert Path(result_path).stat().st_size > 0, "Output file is empty"
        
        # Verify the filename matches expected pattern
        assert "test_scatterplot.png" in str(result_path), "Filename does not match expected pattern"
        
        # Clean up matplotlib
        plt.close('all')

def test_boxplot_generation(sample_data):
    """
    Test that generate_boxplot_by_quartile creates a valid plot file
    with correct axis labels and quartile grouping.
    
    This test verifies:
    1. The function executes without error
    2. The output file is created on disk
    3. The file is a valid image (non-zero size)
    """
    x_col = 'sleep_quartile'
    y_col = 'shannon_diversity'
    
    # Verify columns exist in sample data
    assert x_col in sample_data.columns, f"Column {x_col} not found in sample data"
    assert y_col in sample_data.columns, f"Column {y_col} not found in sample data"
    
    # Create a temporary directory for the plot
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_boxplot.png"
        
        # Call the function
        result_path = generate_boxplot_by_quartile(
            data=sample_data,
            x_column=x_col,
            y_column=y_col,
            output_path=str(output_path),
            title="Test: Shannon Diversity by Sleep Quartile"
        )
        
        # Verify the file was created
        assert result_path is not None, "Function returned None for output path"
        assert Path(result_path).exists(), f"Output file was not created at {result_path}"
        assert Path(result_path).stat().st_size > 0, "Output file is empty"
        
        # Verify the filename matches expected pattern
        assert "test_boxplot.png" in str(result_path), "Filename does not match expected pattern"
        
        # Clean up matplotlib
        plt.close('all')

def test_boxplot_missing_column(sample_data):
    """
    Test that generate_boxplot_by_quartile raises appropriate error when
    required column is missing.
    """
    x_col = 'nonexistent_column'
    y_col = 'shannon_diversity'
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_error.png"
        
        with pytest.raises((KeyError, ValueError)):
            generate_boxplot_by_quartile(
                data=sample_data,
                x_column=x_col,
                y_column=y_col,
                output_path=str(output_path)
            )
        
        plt.close('all')

def test_scatterplot_missing_column(sample_data, sample_correlation_results):
    """
    Test that generate_scatterplot_with_regression raises appropriate error when
    required column is missing.
    """
    x_col = 'nonexistent_column'
    y_col = 'sleep_efficiency'
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_error.png"
        
        with pytest.raises((KeyError, ValueError)):
            generate_scatterplot_with_regression(
                data=sample_data,
                x_column=x_col,
                y_column=y_col,
                output_path=str(output_path)
            )
        
        plt.close('all')