"""
Test suite for T034: Generate holdout_metrics.json.

Verifies that:
1. The report is generated from T033 outputs.
2. The JSON structure matches the specification.
3. The p-value and metric values are correctly propagated.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
# Ensure code/ is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis.holdout_report import (
    load_holdout_metrics_from_permutation,
    compile_final_report,
    save_report,
    generate_holdout_report_pipeline
)
from config import get_path

@pytest.fixture
def mock_permutation_results():
    """Mock data representing T033 output."""
    return {
        "observed_metric": 0.85,
        "p_value": 0.012,
        "n_permutations": 1000,
        "metric_type": "accuracy",
        "null_model_metric": 0.50
    }

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for test outputs."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    return reports_dir

def test_load_permutation_results_success(mock_permutation_results, temp_output_dir):
    """Test loading valid permutation results."""
    input_file = temp_output_dir / "holdout_metrics.json"
    with open(input_file, 'w') as f:
        json.dump(mock_permutation_results, f)
    
    results = load_holdout_metrics_from_permutation(input_file)
    
    assert results['p_value'] == mock_permutation_results['p_value']
    assert results['observed_metric'] == mock_permutation_results['observed_metric']

def test_load_permutation_results_missing_file(temp_output_dir):
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_holdout_metrics_from_permutation(temp_output_dir / "nonexistent.json")

def test_compile_final_report_structure(mock_permutation_results):
    """Test that the compiled report has the correct structure."""
    report = compile_final_report(mock_permutation_results)
    
    assert "model_performance" in report
    assert "statistical_significance" in report
    assert "metadata" in report
    
    # Check specific fields
    assert report["model_performance"]["metric_name"] == "accuracy"
    assert report["model_performance"]["value"] == 0.85
    assert report["statistical_significance"]["p_value"] == 0.012
    assert report["statistical_significance"]["is_significant"] is True
    assert report["model_performance"]["null_model_value"] == 0.50

def test_compile_final_report_significance_threshold(mock_permutation_results):
    """Test significance logic with p > 0.05."""
    mock_permutation_results['p_value'] = 0.06
    report = compile_final_report(mock_permutation_results)
    assert report["statistical_significance"]["is_significant"] is False

def test_save_report_creates_file(mock_permutation_results, temp_output_dir):
    """Test that save_report creates the file."""
    output_file = temp_output_dir / "final_report.json"
    report = compile_final_report(mock_permutation_results)
    
    save_report(report, output_file)
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        saved_data = json.load(f)
    
    assert saved_data["model_performance"]["value"] == 0.85

def test_full_pipeline(mock_permutation_results, temp_output_dir):
    """Test the full pipeline end-to-end."""
    input_file = temp_output_dir / "input_perm.json"
    output_file = temp_output_dir / "final_report.json"
    
    # Write mock input
    with open(input_file, 'w') as f:
        json.dump(mock_permutation_results, f)
    
    # Run pipeline
    result = generate_holdout_report_pipeline(input_file, output_file)
    
    # Verify output exists and matches
    assert output_file.exists()
    with open(output_file, 'r') as f:
        final = json.load(f)
    
    assert final["model_performance"]["value"] == 0.85
    assert final["statistical_significance"]["p_value"] == 0.012