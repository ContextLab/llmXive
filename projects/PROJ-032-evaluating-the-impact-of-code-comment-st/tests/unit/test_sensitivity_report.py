"""
Unit tests for the sensitivity report generation (T032b).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
from analysis import run_sensitivity_analysis, save_sensitivity_report

@pytest.fixture
def sample_metrics_data():
    """Create sample metrics data for testing."""
    return [
        {
            "repo_id": "test_repo_1",
            "readability": 65.3,
            "sentiment": 0.2,
            "density": 0.15,
            "churn": 120.5,
            "bug_fix_rate": 0.1,
            "complexity": 12.3,
            "age": 365,
            "contributors": 5
        },
        {
            "repo_id": "test_repo_2",
            "readability": 45.1,
            "sentiment": -0.1,
            "density": 0.08,
            "churn": 200.0,
            "bug_fix_rate": 0.25,
            "complexity": 18.7,
            "age": 730,
            "contributors": 12
        }
    ]

def test_run_sensitivity_analysis_with_thresholds(sample_metrics_data):
    """Test that run_sensitivity_analysis returns results for multiple thresholds."""
    thresholds = [0.01, 0.05, 0.1]
    results = run_sensitivity_analysis(sample_metrics_data, thresholds)
    
    assert results is not None
    assert isinstance(results, dict)
    assert "thresholds" in results
    assert "results" in results
    
    # Check that all requested thresholds are present
    assert len(results["thresholds"]) == len(thresholds)
    for threshold in thresholds:
        assert threshold in results["thresholds"]
    
    # Check results structure
    results_by_threshold = results["results"]
    for threshold in thresholds:
        assert threshold in results_by_threshold
        threshold_result = results_by_threshold[threshold]
        assert "model_type" in threshold_result
        assert "r_squared" in threshold_result
        assert "p_values" in threshold_result
        assert "is_significant" in threshold_result
        assert "sensitivity_data" in threshold_result

def test_save_sensitivity_report_creates_file(sample_metrics_data):
    """Test that save_sensitivity_report creates a valid JSON file."""
    thresholds = [0.05]
    results = run_sensitivity_analysis(sample_metrics_data, thresholds)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_sensitivity_report.json"
        save_sensitivity_report(results, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == results
        assert "thresholds" in saved_data
        assert "results" in saved_data

def test_save_sensitivity_report_creates_directory_if_needed(sample_metrics_data):
    """Test that save_sensitivity_report creates parent directories if they don't exist."""
    thresholds = [0.05]
    results = run_sensitivity_analysis(sample_metrics_data, thresholds)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "subdir" / "deep" / "test_sensitivity_report.json"
        save_sensitivity_report(results, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == results

def test_sensitivity_analysis_with_single_threshold(sample_metrics_data):
    """Test sensitivity analysis with a single threshold."""
    thresholds = [0.05]
    results = run_sensitivity_analysis(sample_metrics_data, thresholds)
    
    assert results is not None
    assert len(results["thresholds"]) == 1
    assert 0.05 in results["thresholds"]

def test_sensitivity_analysis_empty_data():
    """Test that sensitivity analysis handles empty data gracefully."""
    empty_data = []
    thresholds = [0.05]
    
    # Should return empty or minimal result, not crash
    results = run_sensitivity_analysis(empty_data, thresholds)
    
    # Depending on implementation, this might return empty results or raise
    # For robustness, we expect it to not crash
    assert results is not None
    assert "thresholds" in results