"""
Unit tests for the collinearity check module (T020a).
"""
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest
from scipy import stats

from analysis.collinearity_check import calculate_collinearity, write_summary_to_csv

@pytest.fixture
def mock_variants_file(tmp_path):
    """Create a mock parquet file with test data."""
    # Create a dataset where token_count and structural_element_count are perfectly correlated
    # to ensure a known correlation coefficient
    data = {
        "problem_id": ["p1", "p2", "p3", "p4", "p5"],
        "variant_label": ["simple", "moderate", "complex", "very_complex", "degenerate"],
        "token_count": [100, 200, 300, 400, 500],
        "structural_element_count": [10, 20, 30, 40, 50],
        "dependency_depth": [1, 2, 3, 4, 5]
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "mock_variants.parquet"
    df.to_parquet(file_path)
    return file_path

@pytest.fixture
def mock_variants_file_low_corr(tmp_path):
    """Create a mock parquet file with low/no correlation."""
    # Create a dataset with no correlation
    data = {
        "problem_id": ["p1", "p2", "p3", "p4", "p5"],
        "variant_label": ["simple", "moderate", "complex", "very_complex", "degenerate"],
        "token_count": [100, 200, 300, 400, 500],
        "structural_element_count": [50, 10, 40, 20, 30], # Randomized
        "dependency_depth": [1, 2, 3, 4, 5]
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "mock_variants_low_corr.parquet"
    df.to_parquet(file_path)
    return file_path

def test_calculate_collinearity_perfect_correlation(mock_variants_file):
    """Test that perfectly correlated data yields r=1.0."""
    results = calculate_collinearity(mock_variants_file)
    assert abs(results["pearson_r"] - 1.0) < 1e-5
    assert results["p_value"] < 0.05
    assert results["n_samples"] == 5

def test_calculate_collinearity_low_correlation(mock_variants_file_low_corr):
    """Test that uncorrelated data yields r close to 0."""
    results = calculate_collinearity(mock_variants_file_low_corr)
    # With this specific small dataset, r might not be exactly 0, but should be low
    # and p-value should be high (not significant)
    assert abs(results["pearson_r"]) < 0.5
    assert results["n_samples"] == 5

def test_calculate_collinearity_missing_file(tmp_path):
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        calculate_collinearity(tmp_path / "nonexistent.parquet")

def test_calculate_collinearity_missing_columns(tmp_path):
    """Test that ValueError is raised for missing columns."""
    data = {
        "problem_id": ["p1"],
        "token_count": [100]
        # Missing 'structural_element_count'
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "missing_cols.parquet"
    df.to_parquet(file_path)

    with pytest.raises(ValueError):
        calculate_collinearity(file_path)

def test_write_summary_to_csv_creates_file(tmp_path):
    """Test that write_summary_to_csv creates the file with headers."""
    output_path = tmp_path / "analysis_summary.csv"
    results = {
        "pearson_r": 0.95,
        "p_value": 0.001,
        "n_samples": 10
    }

    written_path = write_summary_to_csv(results, output_path)

    assert written_path.exists()
    df = pd.read_csv(written_path)
    assert len(df) == 1
    assert df["test_type"].iloc[0] == "collinearity_check"
    assert abs(df["correlation_coefficient"].iloc[0] - 0.95) < 1e-5

def test_write_summary_to_csv_appends(tmp_path):
    """Test that write_summary_to_csv appends to existing file."""
    output_path = tmp_path / "analysis_summary.csv"

    # Write first row
    write_summary_to_csv(
        {"pearson_r": 0.5, "p_value": 0.1, "n_samples": 5},
        output_path
    )
    # Write second row
    write_summary_to_csv(
        {"pearson_r": 0.8, "p_value": 0.01, "n_samples": 8},
        output_path
    )

    df = pd.read_csv(output_path)
    assert len(df) == 2
    assert df["test_type"].tolist() == ["collinearity_check", "collinearity_check"]