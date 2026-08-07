"""
Integration test for threshold comparison analysis (T023).

This test verifies that the threshold comparison module correctly:
1. Loads fitted threshold parameters from multiple sparsity patterns
2. Performs statistical comparisons
3. Generates output files (JSON and Markdown report)
4. Handles edge cases (single pattern, missing data)
"""
import os
import json
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.threshold_comparison import (
    load_fitted_thresholds,
    compare_thresholds,
    generate_comparison_report,
    main
)

from utils.config import get_project_paths

@pytest.fixture
def mock_fitted_data():
    """Create mock fitted threshold data for multiple patterns."""
    return {
        "results": {
            "diagonal": {
                "theta_c": 2.05,
                "theta_c_std": 0.02,
                "r_squared": 0.98,
                "n_samples": 1000,
                "fit_params": {"a": 1.0, "b": 2.05, "c": 0.5},
                "confidence_interval_95": [2.01, 2.09]
            },
            "random_sparse": {
                "theta_c": 2.12,
                "theta_c_std": 0.03,
                "r_squared": 0.97,
                "n_samples": 1000,
                "fit_params": {"a": 1.0, "b": 2.12, "c": 0.5},
                "confidence_interval_95": [2.06, 2.18]
            },
            "block_sparse": {
                "theta_c": 2.08,
                "theta_c_std": 0.025,
                "r_squared": 0.96,
                "n_samples": 1000,
                "fit_params": {"a": 1.0, "b": 2.08, "c": 0.5},
                "confidence_interval_95": [2.03, 2.13]
            }
        }
    }

@pytest.fixture
def temp_processed_dir(tmp_path):
    """Create a temporary processed directory with mock data."""
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    
    # Create mock fit_params.json
    fit_params = {
        "results": {
            "diagonal": {
                "theta_c": 2.05,
                "theta_c_std": 0.02,
                "r_squared": 0.98,
                "n_samples": 1000
            },
            "random_sparse": {
                "theta_c": 2.12,
                "theta_c_std": 0.03,
                "r_squared": 0.97,
                "n_samples": 1000
            }
        }
    }
    
    fit_file = processed_dir / "threshold_fit_params.json"
    with open(fit_file, 'w') as f:
        json.dump(fit_params, f)
    
    return processed_dir

def test_load_fitted_thresholds_success(temp_processed_dir, mock_fitted_data):
    """Test successful loading of fitted thresholds."""
    # Mock the get_project_paths to return our temp directory
    with patch('analysis.threshold_comparison.get_project_paths') as mock_paths:
        mock_paths.return_value = {"processed": temp_processed_dir}
        
        results = load_fitted_thresholds()
        
        assert "diagonal" in results
        assert "random_sparse" in results
        assert results["diagonal"]["theta_c"] == 2.05
        assert results["random_sparse"]["theta_c_std"] == 0.03
        assert len(results) == 2

def test_load_fitted_thresholds_missing_file(tmp_path):
    """Test error handling when fit file is missing."""
    with patch('analysis.threshold_comparison.get_project_paths') as mock_paths:
        mock_paths.return_value = {"processed": tmp_path}
        
        with pytest.raises(FileNotFoundError, match="Fitted parameters file not found"):
            load_fitted_thresholds()

def test_load_fitted_thresholds_no_results(tmp_path, mock_fitted_data):
    """Test error handling when no results found."""
    # Create empty results file
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    fit_file = processed_dir / "threshold_fit_params.json"
    with open(fit_file, 'w') as f:
        json.dump({"results": {}}, f)
    
    with patch('analysis.threshold_comparison.get_project_paths') as mock_paths:
        mock_paths.return_value = {"processed": processed_dir}
        
        with pytest.raises(ValueError, match="No fitted threshold results found"):
            load_fitted_thresholds()

def test_compare_thresholds_basic(mock_fitted_data):
    """Test basic threshold comparison functionality."""
    comparison = compare_thresholds(mock_fitted_data["results"], reference_pattern="diagonal")
    
    assert comparison["reference_pattern"] == "diagonal"
    assert comparison["reference_theta_c"] == 2.05
    assert comparison["n_patterns_compared"] == 2
    assert "random_sparse" in comparison["patterns"]
    assert "block_sparse" in comparison["patterns"]
    
    # Check comparisons list
    assert len(comparison["comparisons"]) == 2
    
    # Check specific comparison values
    random_sparse_comp = next(c for c in comparison["comparisons"] if c["pattern"] == "random_sparse")
    assert random_sparse_comp["theta_c"] == 2.12
    assert abs(random_sparse_comp["difference"]) == pytest.approx(0.07, rel=0.1)
    assert "z_score" in random_sparse_comp
    assert "p_value" in random_sparse_comp

def test_compare_thresholds_single_pattern(mock_fitted_data):
    """Test error handling with only one pattern."""
    single_pattern_data = {"diagonal": mock_fitted_data["results"]["diagonal"]}
    
    with pytest.raises(ValueError, match="Need at least 2 sparsity patterns"):
        compare_thresholds(single_pattern_data)

def test_compare_thresholds_invalid_reference(mock_fitted_data):
    """Test error handling with invalid reference pattern."""
    with pytest.raises(ValueError, match="Reference pattern 'nonexistent' not found"):
        compare_thresholds(mock_fitted_data["results"], reference_pattern="nonexistent")

def test_generate_comparison_report(mock_fitted_data):
    """Test report generation."""
    comparison = compare_thresholds(mock_fitted_data["results"], reference_pattern="diagonal")
    report = generate_comparison_report(comparison)
    
    assert "# Threshold Comparison Report" in report
    assert "Reference pattern: **diagonal**" in report
    assert "Overall Statistics" in report
    assert "Pairwise Comparisons" in report
    assert "Key Findings" in report
    assert "random_sparse" in report
    assert "block_sparse" in report
    assert "Methodology" in report
    assert "Limitations" in report

def test_main_integration(temp_processed_dir, mock_fitted_data):
    """Test the main function end-to-end."""
    # Update the mock file with more patterns
    fit_params = {
        "results": {
            "diagonal": {
                "theta_c": 2.05,
                "theta_c_std": 0.02,
                "r_squared": 0.98,
                "n_samples": 1000
            },
            "random_sparse": {
                "theta_c": 2.12,
                "theta_c_std": 0.03,
                "r_squared": 0.97,
                "n_samples": 1000
            }
        }
    }
    
    fit_file = temp_processed_dir / "threshold_fit_params.json"
    with open(fit_file, 'w') as f:
        json.dump(fit_params, f)
    
    with patch('analysis.threshold_comparison.get_project_paths') as mock_paths:
        mock_paths.return_value = {"processed": temp_processed_dir}
        
        result = main()
        
        # Verify outputs were created
        json_output = temp_processed_dir / "threshold_comparison_results.json"
        report_output = temp_processed_dir / "threshold_comparison_report.md"
        
        assert json_output.exists()
        assert report_output.exists()
        
        # Verify JSON content
        with open(json_output, 'r') as f:
            saved_json = json.load(f)
        
        assert saved_json["reference_pattern"] == "diagonal"
        assert saved_json["n_patterns_compared"] == 1
        
        # Verify report content
        with open(report_output, 'r') as f:
            saved_report = f.read()
        
        assert "# Threshold Comparison Report" in saved_report
        assert "diagonal" in saved_report
        assert "random_sparse" in saved_report

def test_main_missing_data(tmp_path):
    """Test main function with missing data."""
    with patch('analysis.threshold_comparison.get_project_paths') as mock_paths:
        mock_paths.return_value = {"processed": tmp_path}
        
        with pytest.raises(FileNotFoundError):
            main()

def test_report_formatting(mock_fitted_data):
    """Test that the report has proper markdown formatting."""
    comparison = compare_thresholds(mock_fitted_data["results"], reference_pattern="diagonal")
    report = generate_comparison_report(comparison)
    
    # Check for markdown table syntax
    assert "| Pattern |" in report
    assert "|---------|" in report
    
    # Check for proper heading levels
    assert "## Summary" in report
    assert "## Overall Statistics" in report
    assert "## Pairwise Comparisons" in report
    assert "## Key Findings" in report
    
    # Check for specific values in report
    assert "2.05" in report  # Reference theta_c
    assert "2.12" in report  # Random sparse theta_c
