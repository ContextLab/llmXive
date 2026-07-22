import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Mock the config paths before importing the module
import code.config
original_get_results_path = code.config.get_results_path
original_get_processed_path = code.config.get_processed_path
original_get_data_path = code.config.get_data_path

def mock_get_results_path():
    return os.path.join(os.getcwd(), "results")

def mock_get_processed_path():
    return os.path.join(os.getcwd(), "data", "processed")

def mock_get_data_path():
    return os.path.join(os.getcwd(), "data")

code.config.get_results_path = mock_get_results_path
code.config.get_processed_path = mock_get_processed_path
code.config.get_data_path = mock_get_data_path

from code.verify_results import (
    validate_statistical_significance,
    validate_logistic_regression,
    validate_sensitivity_report,
    verify_results_completeness
)

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = os.path.join(tmpdir, "results")
        processed_dir = os.path.join(tmpdir, "data", "processed")
        os.makedirs(results_dir)
        os.makedirs(processed_dir)
        yield results_dir, processed_dir

def test_validate_statistical_significance_valid():
    """Test validation with valid statistical significance data."""
    data = {
        "mcnemar_tests": {
            "complexity": {"p_value": 0.045, "statistic": 3.84},
            "loc": {"p_value": 0.12, "statistic": 2.45}
        }
    }
    assert validate_statistical_significance(data) is True

def test_validate_statistical_significance_empty():
    """Test validation with empty data."""
    assert validate_statistical_significance({}) is False
    assert validate_statistical_significance(None) is False

def test_validate_statistical_significance_invalid_structure():
    """Test validation with invalid structure."""
    data = {"invalid": "string"}
    assert validate_statistical_significance(data) is False

def test_validate_logistic_regression_valid():
    """Test validation with valid logistic regression data."""
    data = {
        "coefficients": {"loc": 0.5, "cyclomatic": 1.2},
        "vif_scores": {"loc": 1.5, "cyclomatic": 2.1}
    }
    assert validate_logistic_regression(data) is True

def test_validate_logistic_regression_missing_vif():
    """Test validation with missing VIF."""
    data = {
        "coefficients": {"loc": 0.5}
    }
    assert validate_logistic_regression(data) is False

def test_validate_sensitivity_report_valid():
    """Test validation with valid sensitivity report content."""
    content = """
    # Sensitivity Report

    ## Smells detected only by static analysis
    - Long Method

    ## Smells detected only by LLM
    - Duplicate Code

    ## Sensitivity Analysis Results
    LOC threshold 50: 85% accuracy
    """
    assert validate_sensitivity_report(content) is True

def test_validate_sensitivity_report_missing_sections():
    """Test validation with missing sections."""
    content = """
    # Sensitivity Report
    Only static smells listed here.
    """
    assert validate_sensitivity_report(content) is False

def test_verify_results_completeness_missing_files(temp_dirs):
    """Test verification when required files are missing."""
    results_dir, processed_dir = temp_dirs
    
    # Create empty processed file
    processed_file = os.path.join(processed_dir, "semantic_results.json")
    with open(processed_file, 'w') as f:
        json.dump([{"id": 1}], f)
    
    # Do not create result files
    with patch('code.verify_results.get_results_path', return_value=results_dir), \
         patch('code.verify_results.get_processed_path', return_value=processed_dir):
        success = verify_results_completeness()
        assert success is False

def test_verify_results_completeness_invalid_json(temp_dirs):
    """Test verification with invalid JSON in results."""
    results_dir, processed_dir = temp_dirs
    
    # Create processed file
    processed_file = os.path.join(processed_dir, "semantic_results.json")
    with open(processed_file, 'w') as f:
        json.dump([{"id": i} for i in range(100)], f)
    
    # Create invalid statistical significance file
    stat_file = os.path.join(results_dir, "statistical_significance.json")
    with open(stat_file, 'w') as f:
        f.write("invalid json")
    
    # Create valid logistic regression file
    lr_file = os.path.join(results_dir, "logistic_regression.json")
    with open(lr_file, 'w') as f:
        json.dump({"coefficients": {"loc": 1}, "vif_scores": {"loc": 1}}, f)
    
    # Create valid sensitivity report
    sens_file = os.path.join(results_dir, "sensitivity_report.md")
    with open(sens_file, 'w') as f:
        f.write("only by static\nonly by LLM\nsensitivity")
    
    with patch('code.verify_results.get_results_path', return_value=results_dir), \
         patch('code.verify_results.get_processed_path', return_value=processed_dir):
        success = verify_results_completeness()
        assert success is False
