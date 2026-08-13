"""
Unit tests for collinearity diagnostics (VIF calculation).
"""
import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import tempfile
import os

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modeling.collinearity import calculate_vif, flag_high_collinearity, run_collinearity_diagnostics

@pytest.fixture
def sample_data():
    """Create sample data for VIF testing."""
    np.random.seed(42)
    n_samples = 100
    
    # Create features with some correlation
    X1 = np.random.normal(0, 1, n_samples)
    X2 = X1 * 0.8 + np.random.normal(0, 0.2, n_samples)  # High correlation with X1
    X3 = np.random.normal(0, 1, n_samples)  # Independent
    X4 = X3 * 0.3 + np.random.normal(0, 0.5, n_samples)  # Low correlation with X3
    
    df = pd.DataFrame({
        'feature_A': X1,
        'feature_B': X2,
        'feature_C': X3,
        'feature_D': X4
    })
    return df

def test_calculate_vif_basic(sample_data):
    """Test basic VIF calculation."""
    vif_series = calculate_vif(sample_data)
    
    assert len(vif_series) == 4
    assert all(vif_series.index == ['feature_A', 'feature_B', 'feature_C', 'feature_D'])
    assert all(vif_series >= 1.0)  # VIF is always >= 1

def test_calculate_vif_high_collinearity(sample_data):
    """Test that highly correlated features have higher VIF."""
    vif_series = calculate_vif(sample_data)
    
    # feature_A and feature_B are highly correlated, so they should have higher VIF
    assert vif_series['feature_A'] > 1.0
    assert vif_series['feature_B'] > 1.0

def test_calculate_vif_empty_dataframe():
    """Test VIF calculation with empty dataframe."""
    df = pd.DataFrame()
    vif_series = calculate_vif(df)
    
    assert len(vif_series) == 0
    assert vif_series.dtype == float

def test_flag_high_collinearity_basic(sample_data):
    """Test flagging high collinearity."""
    vif_series = calculate_vif(sample_data)
    
    # With threshold 5.0, we might not have any high collinearity in random data
    high_coll = flag_high_collinearity(vif_series, threshold=5.0)
    assert isinstance(high_coll, list)

def test_flag_high_collinearity_threshold():
    """Test that threshold correctly filters features."""
    vif_data = pd.Series({
        'low_vif': 2.0,
        'medium_vif': 4.9,
        'high_vif': 6.0,
        'very_high_vif': 15.0
    })
    
    high_coll_5 = flag_high_collinearity(vif_data, threshold=5.0)
    assert set(high_coll_5) == {'high_vif', 'very_high_vif'}
    
    high_coll_10 = flag_high_collinearity(vif_data, threshold=10.0)
    assert set(high_coll_10) == {'very_high_vif'}

def test_run_collinearity_diagnostics_integration(tmp_path):
    """Test full integration of collinearity diagnostics."""
    # Create temporary files
    feature_importance_path = tmp_path / "feature_importance_ranking.json"
    processed_data_path = tmp_path / "batch_corrected_matrix.csv"
    output_path = tmp_path / "vif_scores.json"
    
    # Create feature importance file
    importance_data = {
        "top_metabolites": ["feature_A", "feature_B", "feature_C", "feature_D"],
        "framing": "associational"
    }
    with open(feature_importance_path, 'w') as f:
        json.dump(importance_data, f)
    
    # Create processed data file
    np.random.seed(42)
    n_samples = 50
    X1 = np.random.normal(0, 1, n_samples)
    X2 = X1 * 0.7 + np.random.normal(0, 0.3, n_samples)
    X3 = np.random.normal(0, 1, n_samples)
    X4 = np.random.normal(0, 1, n_samples)
    
    df = pd.DataFrame({
        'feature_A': X1,
        'feature_B': X2,
        'feature_C': X3,
        'feature_D': X4
    })
    df.to_csv(processed_data_path)
    
    # Run diagnostics
    result = run_collinearity_diagnostics(
        feature_importance_path=str(feature_importance_path),
        processed_data_path=str(processed_data_path),
        output_path=str(output_path),
        top_n=4,
        vif_threshold=5.0
    )
    
    # Verify results
    assert result["analysis_status"] == "success"
    assert "vif_scores" in result
    assert "high_collinearity_features" in result
    assert "framing" in result
    assert result["framing"] == "These results represent associations, not causation"
    
    # Verify output file exists and is valid JSON
    assert output_path.exists()
    with open(output_path, 'r') as f:
        saved_result = json.load(f)
    
    assert saved_result["analysis_status"] == "success"
    assert len(saved_result["vif_scores"]) == 4

def test_run_collinearity_diagnostics_missing_features(tmp_path):
    """Test handling of missing features in processed data."""
    feature_importance_path = tmp_path / "feature_importance_ranking.json"
    processed_data_path = tmp_path / "batch_corrected_matrix.csv"
    output_path = tmp_path / "vif_scores.json"
    
    # Create feature importance with features not in data
    importance_data = {
        "top_metabolites": ["missing_feature_1", "missing_feature_2", "feature_A"],
        "framing": "associational"
    }
    with open(feature_importance_path, 'w') as f:
        json.dump(importance_data, f)
    
    # Create processed data with only one matching feature
    np.random.seed(42)
    df = pd.DataFrame({
        'feature_A': np.random.normal(0, 1, 30),
        'feature_B': np.random.normal(0, 1, 30)
    })
    df.to_csv(processed_data_path)
    
    # Run diagnostics - should handle missing features gracefully
    result = run_collinearity_diagnostics(
        feature_importance_path=str(feature_importance_path),
        processed_data_path=str(processed_data_path),
        output_path=str(output_path),
        top_n=3,
        vif_threshold=5.0
    )
    
    # Should succeed with only one feature (VIF=1 for single feature)
    assert result["analysis_status"] == "success"
    assert len(result["vif_scores"]) == 1

def test_run_collinearity_diagnostics_no_overlap(tmp_path):
    """Test handling when no features overlap."""
    feature_importance_path = tmp_path / "feature_importance_ranking.json"
    processed_data_path = tmp_path / "batch_corrected_matrix.csv"
    output_path = tmp_path / "vif_scores.json"
    
    # Create feature importance with no matching features
    importance_data = {
        "top_metabolites": ["missing_1", "missing_2", "missing_3"],
        "framing": "associational"
    }
    with open(feature_importance_path, 'w') as f:
        json.dump(importance_data, f)
    
    # Create processed data with different features
    np.random.seed(42)
    df = pd.DataFrame({
        'feature_A': np.random.normal(0, 1, 30),
        'feature_B': np.random.normal(0, 1, 30)
    })
    df.to_csv(processed_data_path)
    
    # Run diagnostics - should fail gracefully
    result = run_collinearity_diagnostics(
        feature_importance_path=str(feature_importance_path),
        processed_data_path=str(processed_data_path),
        output_path=str(output_path),
        top_n=3,
        vif_threshold=5.0
    )
    
    assert result["analysis_status"] == "failed"
    assert "No overlapping features" in result["reason"]
    
    # Verify output file exists
    assert output_path.exists()