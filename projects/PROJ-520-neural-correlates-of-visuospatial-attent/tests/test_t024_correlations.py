"""
Tests for T024: Correlation Analysis
"""
import pytest
import os
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd

from code.analyze_correlations import (
    load_feature_matrix,
    compute_correlation_matrix,
    compute_variance_inflation_factors,
    compute_feature_stats,
    run_correlation_analysis
)
from code.config import get_paths

@pytest.fixture
def sample_feature_df():
    """Create a sample feature DataFrame for testing."""
    np.random.seed(42)
    n_epochs = 100
    data = {
        'alpha_P3': np.random.randn(n_epochs),
        'alpha_Pz': np.random.randn(n_epochs) * 0.9 + np.random.randn(n_epochs) * 0.1,  # High correlation
        'alpha_P4': np.random.randn(n_epochs),
        'beta_F3': np.random.randn(n_epochs),
        'beta_Fz': np.random.randn(n_epochs) * 0.3 + np.random.randn(n_epochs) * 0.7,
        'beta_F4': np.random.randn(n_epochs),
        'label': np.random.choice([0, 1], n_epochs)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_file(sample_feature_df, tmp_path):
    """Save sample DataFrame to a temporary CSV file."""
    csv_path = tmp_path / "test_features.csv"
    sample_feature_df.to_csv(csv_path, index=False)
    return csv_path

def test_load_feature_matrix(temp_csv_file):
    """Test loading feature matrix from CSV."""
    df = load_feature_matrix(temp_csv_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 100
    assert 'alpha_P3' in df.columns
    assert df['alpha_P3'].dtype == np.float64

def test_load_feature_matrix_missing_file(tmp_path):
    """Test error handling for missing file."""
    missing_path = tmp_path / "nonexistent.csv"
    with pytest.raises(FileNotFoundError):
        load_feature_matrix(missing_path)

def test_compute_correlation_matrix(temp_csv_file):
    """Test correlation matrix computation."""
    df = load_feature_matrix(temp_csv_file)
    result = compute_correlation_matrix(df)
    
    assert "correlation_matrix" in result
    assert "high_correlation_pairs" in result
    assert "matrix_shape" in result
    
    # Check that high correlation pairs are detected (alpha_P3 and alpha_Pz)
    high_corr = result["high_correlation_pairs"]
    assert len(high_corr) > 0
    
    # Verify the specific pair is detected
    pair_found = False
    for pair in high_corr:
        if ('alpha_P3' in [pair["feature_1"], pair["feature_2"]] and 
            'alpha_Pz' in [pair["feature_1"], pair["feature_2"]]):
            pair_found = True
            assert abs(pair["correlation"]) > 0.8
    assert pair_found

def test_compute_variance_inflation_factors(temp_csv_file):
    """Test VIF computation."""
    df = load_feature_matrix(temp_csv_file)
    result = compute_variance_inflation_factors(df)
    
    assert "vif_scores" in result
    assert "threshold" in result
    assert result["threshold"] == 5.0
    
    # Check that VIF scores are computed for all features
    assert len(result["vif_scores"]) == len(df.select_dtypes(include=[np.number]).columns)

def test_compute_feature_stats(temp_csv_file):
    """Test feature statistics computation."""
    df = load_feature_matrix(temp_csv_file)
    result = compute_feature_stats(df)
    
    assert isinstance(result, dict)
    assert "alpha_P3" in result
    
    # Check required statistics
    stats = result["alpha_P3"]
    assert "mean" in stats
    assert "std" in stats
    assert "min" in stats
    assert "max" in stats
    assert "median" in stats
    assert "skewness" in stats
    assert "kurtosis" in stats

def test_run_correlation_analysis(temp_csv_file, tmp_path):
    """Test full correlation analysis pipeline."""
    output_json = tmp_path / "feature_metadata.json"
    
    result = run_correlation_analysis(temp_csv_file, output_json, seed=42)
    
    # Verify output file exists
    assert output_json.exists()
    
    # Verify JSON structure
    with open(output_json, 'r') as f:
        metadata = json.load(f)
    
    assert metadata["task_id"] == "T024"
    assert "correlation_analysis" in metadata
    assert "collinearity_analysis" in metadata
    assert "feature_statistics" in metadata
    assert "summary" in metadata
    
    # Verify summary counts
    assert metadata["summary"]["high_correlation_pairs_count"] >= 0
    assert metadata["summary"]["high_vif_features_count"] >= 0

def test_empty_dataframe(tmp_path):
    """Test handling of empty or non-numeric data."""
    df = pd.DataFrame({'label': [0, 1, 2]})  # No numeric features
    csv_path = tmp_path / "empty_numeric.csv"
    df.to_csv(csv_path, index=False)
    
    corr_result = compute_correlation_matrix(df)
    assert "error" in corr_result
    
    vif_result = compute_variance_inflation_factors(df)
    assert "error" in vif_result
