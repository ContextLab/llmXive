import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock the config paths to use a temporary directory
@pytest.fixture
def mock_paths(tmp_path):
    processed_dir = tmp_path / "processed"
    results_dir = tmp_path / "results"
    raw_dir = tmp_path / "raw"
    
    processed_dir.mkdir()
    results_dir.mkdir()
    raw_dir.mkdir()
    
    # Create mock data files that the report generator expects
    # 1. Model Metrics (T020)
    metrics_data = {
        "mean_pearson_r": 0.45,
        "mean_r_squared": 0.20,
        "std_pearson_r": 0.05,
        "std_r_squared": 0.02,
        "n_folds": 5
    }
    with open(processed_dir / "model_metrics.json", 'w') as f:
        json.dump(metrics_data, f)
    
    # 2. Permutation P-Value (T022)
    perm_data = {"p_value": 0.012}
    with open(results_dir / "permutation_p_value.json", 'w') as f:
        json.dump(perm_data, f)
    
    # 3. Bootstrap CI (T023)
    ci_data = {
        "ci_95_lower": 0.15,
        "ci_95_upper": 0.25,
        "mean_r2": 0.20
    }
    with open(processed_dir / "bootstrap_ci.json", 'w') as f:
        json.dump(ci_data, f)
    
    # 4. Sensitivity Analysis (T024)
    sens_data = {
        "rows": [
            {"variance_threshold": 0.01, "pca_retention": 0.95, "r2": 0.21},
            {"variance_threshold": 0.05, "pca_retention": 0.90, "r2": 0.22}
        ],
        "incomplete": False,
        "time_budget_exceeded": False
    }
    with open(processed_dir / "sensitivity_analysis.json", 'w') as f:
        json.dump(sens_data, f)
    
    return {
        "processed_dir": str(processed_dir),
        "results_dir": str(results_dir),
        "raw_dir": str(raw_dir)
    }

@pytest.fixture
def mock_config(mock_paths):
    """Patch the get_paths function to return our mock paths."""
    with patch('modeling.report_generator.get_paths') as mock_get:
        mock_get.return_value = {
            'processed_dir': Path(mock_paths['processed_dir']),
            'results_dir': Path(mock_paths['results_dir']),
            'raw_dir': Path(mock_paths['raw_dir'])
        }
        yield mock_get

def test_report_generation(mock_config):
    """Test that the report generator creates a valid JSON file with all required fields."""
    from modeling.report_generator import generate_result_report
    
    # Run the generator
    success = generate_result_report()
    assert success, "Report generation failed"
    
    # Check the output file exists
    paths = mock_config.return_value
    output_file = paths['results_dir'] / 'ResultReport.json'
    assert output_file.exists(), "ResultReport.json was not created"
    
    # Load and validate content
    with open(output_file, 'r') as f:
        report = json.load(f)
    
    # Verify structure
    assert "report_metadata" in report
    assert "model_performance" in report
    assert "statistical_significance" in report
    assert "sensitivity_analysis" in report
    
    # Verify specific values match mocks
    assert report["model_performance"]["mean_pearson_r"] == 0.45
    assert report["model_performance"]["mean_r_squared"] == 0.20
    assert report["statistical_significance"]["permutation_test"]["p_value"] == 0.012
    assert report["statistical_significance"]["permutation_test"]["note"] == "Approximate p-value derived from subset (Plan Override of FR-006)"
    assert report["sensitivity_analysis"]["completed"] is True
    
    # Verify the note about approximation is present
    assert any("approximation" in note.lower() for note in report["data_notes"])

def test_missing_files_handling(mock_config):
    """Test behavior when some input files are missing."""
    # Remove the sensitivity file to test fallback
    paths = mock_config.return_value
    sens_file = paths['processed_dir'] / 'sensitivity_analysis.json'
    if sens_file.exists():
        sens_file.unlink()
    
    from modeling.report_generator import generate_result_report
    
    # Should still succeed but with incomplete sensitivity analysis
    success = generate_result_report()
    assert success, "Report generation should handle missing files gracefully"
    
    output_file = paths['results_dir'] / 'ResultReport.json'
    with open(output_file, 'r') as f:
        report = json.load(f)
    
    # Sensitivity should be marked incomplete
    assert report["sensitivity_analysis"]["completed"] is False
    assert len(report["sensitivity_analysis"]["results"]) == 0
