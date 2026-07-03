"""
Unit tests for Pearson correlation analysis (T033a).

Tests the core logic of computing Pearson correlation between feature
importance and thermal conductivity without requiring full pipeline execution.
"""
import json
import pickle
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pytest

# Import the functions to test
from analysis.pearson_correlation import (
    load_feature_importance_data,
    load_thermal_conductivity_data,
    align_data,
    compute_pearson_correlation,
    generate_correlation_report
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_load_feature_importance_data(temp_dir):
    """Test loading feature importance data from JSON."""
    # Create mock data
    mock_data = {
        "sample_1": [0.1, 0.2, 0.3],
        "sample_2": [0.4, 0.5, 0.6]
    }
    
    file_path = temp_dir / "feature_importance.json"
    with open(file_path, 'w') as f:
        json.dump(mock_data, f)
    
    result = load_feature_importance_data(file_path)
    
    assert result == mock_data
    assert "sample_1" in result
    assert len(result["sample_1"]) == 3

def test_load_feature_importance_data_not_found(temp_dir):
    """Test error handling when file is missing."""
    file_path = temp_dir / "nonexistent.json"
    
    with pytest.raises(FileNotFoundError):
        load_feature_importance_data(file_path)

def test_load_thermal_conductivity_data(temp_dir):
    """Test loading conductivity data from pickle files."""
    # Create mock thermal samples
    sample_1 = {"id": "sample_1", "conductivity": 1.5}
    sample_2 = {"id": "sample_2", "conductivity": 2.0}
    
    with open(temp_dir / "sample_1.pkl", 'wb') as f:
        pickle.dump(sample_1, f)
    with open(temp_dir / "sample_2.pkl", 'wb') as f:
        pickle.dump(sample_2, f)
    
    result = load_thermal_conductivity_data(temp_dir)
    
    assert "sample_1" in result
    assert "sample_2" in result
    assert result["sample_1"] == 1.5
    assert result["sample_2"] == 2.0

def test_load_thermal_conductivity_data_missing_key(temp_dir):
    """Test handling of samples missing conductivity key."""
    sample_1 = {"id": "sample_1"}  # No conductivity
    
    with open(temp_dir / "sample_1.pkl", 'wb') as f:
        pickle.dump(sample_1, f)
    
    result = load_thermal_conductivity_data(temp_dir)
    
    assert "sample_1" not in result

def test_align_data():
    """Test alignment of feature and conductivity data."""
    feature_data = {
        "sample_1": [0.1, 0.2],
        "sample_2": [0.3, 0.4],
        "sample_3": [0.5, 0.6]
    }
    
    conductivity_data = {
        "sample_2": 1.5,
        "sample_3": 2.0,
        "sample_4": 2.5  # Not in feature data
    }
    
    sample_ids, feature_matrix, cond_values = align_data(feature_data, conductivity_data)
    
    assert len(sample_ids) == 2
    assert "sample_2" in sample_ids
    assert "sample_3" in sample_ids
    
    assert len(feature_matrix) == 2
    assert feature_matrix[0] == [0.3, 0.4]
    assert cond_values[0] == 1.5

def test_align_data_no_common(temp_dir):
    """Test error when no common samples exist."""
    feature_data = {"sample_1": [0.1]}
    conductivity_data = {"sample_2": 1.5}
    
    with pytest.raises(ValueError, match="No common samples"):
        align_data(feature_data, conductivity_data)

def test_compute_pearson_correlation():
    """Test Pearson correlation computation."""
    # Perfect positive correlation
    feature_matrix = [[1.0, 2.0], [2.0, 3.0], [3.0, 4.0]]
    conductivity_values = [1.0, 2.0, 3.0]
    
    results = compute_pearson_correlation(feature_matrix, conductivity_values)
    
    # Feature 0 should be perfectly correlated (r=1.0)
    assert np.isclose(results["feature_0"]["r"], 1.0)
    assert results["feature_0"]["p_value"] < 0.05
    
    # Feature 1 should also be perfectly correlated
    assert np.isclose(results["feature_1"]["r"], 1.0)

def test_compute_pearson_correlation_insufficient_data():
    """Test handling of insufficient data points."""
    feature_matrix = [[1.0]]  # Only one sample
    conductivity_values = [1.0]
    
    results = compute_pearson_correlation(feature_matrix, conductivity_values)
    
    assert np.isnan(results["feature_0"]["r"])

def test_generate_correlation_report():
    """Test report generation."""
    sample_ids = ["s1", "s2"]
    correlation_results = {
        "feature_0": {"r": 0.9, "p_value": 0.01},
        "feature_1": {"r": 0.2, "p_value": 0.5}
    }
    
    report = generate_correlation_report(sample_ids, correlation_results)
    
    assert report["sample_count"] == 2
    assert report["features_analyzed"] == 2
    assert "summary" in report
    assert report["summary"]["significant_correlations_count"] == 1