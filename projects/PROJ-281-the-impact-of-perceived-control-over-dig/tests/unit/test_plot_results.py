"""
Unit tests for the visualization module (plot_results.py).
"""
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Import the module under test
from code.viz.plot_results import (
    load_analysis_data,
    calculate_regression_line,
    generate_scatter_plot,
    run_visualization_pipeline
)

@pytest.fixture
def sample_data_csv(tmp_path):
    """Create a temporary CSV file with sample data for testing."""
    data = {
        'post_id': [1, 2, 3, 4, 5],
        'user_id': ['u1', 'u2', 'u3', 'u4', 'u5'],
        'control_proxy': [0.1, 0.5, 0.8, 0.2, 0.9],
        'anxiety_score': [2.1, 1.5, 0.8, 2.0, 0.5],
        'confidence_score': [0.8, 0.9, 0.95, 0.7, 0.85]
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "final_analysis.csv"
    df.to_csv(csv_path, index=False)
    return csv_path

@pytest.fixture
def empty_data_csv(tmp_path):
    """Create a temporary CSV file with no data."""
    csv_path = tmp_path / "empty_analysis.csv"
    pd.DataFrame(columns=['control_proxy', 'anxiety_score']).to_csv(csv_path, index=False)
    return csv_path

@pytest.fixture
def missing_cols_csv(tmp_path):
    """Create a temporary CSV file with missing required columns."""
    csv_path = tmp_path / "missing_cols.csv"
    pd.DataFrame({'other_col': [1, 2, 3]}).to_csv(csv_path, index=False)
    return csv_path

def test_load_analysis_data_valid(sample_data_csv):
    """Test loading valid data."""
    df = load_analysis_data(sample_data_csv)
    assert len(df) == 5
    assert 'control_proxy' in df.columns
    assert 'anxiety_score' in df.columns

def test_load_analysis_data_missing_file(tmp_path):
    """Test loading from a non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        load_analysis_data(tmp_path / "non_existent.csv")

def test_load_analysis_data_missing_columns(missing_cols_csv):
    """Test loading data with missing required columns raises error."""
    with pytest.raises(ValueError):
        load_analysis_data(missing_cols_csv)

def test_calculate_regression_line_basic():
    """Test regression line calculation with simple linear data."""
    x = np.array([1, 2, 3, 4, 5])
    y = np.array([2, 4, 6, 8, 10])  # Perfect linear relationship
    
    slope, intercept = calculate_regression_line(x, y)
    
    assert np.isclose(slope, 2.0, atol=0.01)
    assert np.isclose(intercept, 0.0, atol=0.01)

def test_generate_scatter_plot_creates_file(sample_data_csv, tmp_path):
    """Test that generate_scatter_plot creates a valid image file."""
    df = load_analysis_data(sample_data_csv)
    output_path = tmp_path / "test_plot.png"
    
    generate_scatter_plot(df, output_path)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_run_visualization_pipeline_integration(sample_data_csv, tmp_path):
    """Test the full pipeline from input to output."""
    output_path = tmp_path / "pipeline_output.png"
    
    result_path = run_visualization_pipeline(
        input_data_path=sample_data_csv,
        output_path=output_path
    )
    
    assert result_path == output_path
    assert output_path.exists()
    assert output_path.stat().st_size > 0