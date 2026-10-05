import json
import os
import tempfile
from pathlib import Path
import pytest

# Mock config for testing if necessary, or rely on environment
# We will create temporary files to simulate the inputs

def test_generate_research_report_structure(tmp_path):
    """Test that the generated report contains all required sections."""
    # Setup temporary files
    data_gap_file = tmp_path / "data_gap_status.json"
    results_file = tmp_path / "results.json"
    metrics_file = tmp_path / "metrics.json"
    perm_file = tmp_path / "permutation_results.json"
    thresh_file = tmp_path / "threshold_sensitivity.json"
    output_file = tmp_path / "research.md"

    # Mock Data
    data_gap_file.write_text(json.dumps({"status": "PASS", "missing_sources": []}))
    results_file.write_text(json.dumps({
        "roc_auc": 0.85,
        "performance_status": "PASS"
    }))
    metrics_file.write_text(json.dumps({
        "auprc": 0.78,
        "independent_data_available": True
    }))
    perm_file.write_text(json.dumps({
        "n_permutations": 1000,
        "ranking": [
            {"feature": "DHW", "importance": 0.45, "p_value_corrected": 0.001},
            {"feature": "Thermal_Tolerance", "importance": 0.32, "p_value_corrected": 0.005}
        ],
        "stability_scores": {
            "DHW": 0.92,
            "Thermal_Tolerance": 0.88
        }
    }))
    thresh_file.write_text(json.dumps({
        "thresholds": [
            {"threshold": 0.3, "fp_rate": 0.1, "fn_rate": 0.2},
            {"threshold": 0.5, "fp_rate": 0.05, "fn_rate": 0.3},
            {"threshold": 0.7, "fp_rate": 0.01, "fn_rate": 0.4}
        ],
        "delta_fp": 0.09,
        "delta_fn": 0.2
    }))

    # Mock config module
    import sys
    from types import ModuleType
    
    config_mock = ModuleType('config')
    config_mock.PROJECT_ROOT = str(tmp_path)
    sys.modules['config'] = config_mock

    # Import the function
    from generate_research_report import generate_research_report, load_json_safe

    # Load data as the main function would
    data_gap_status = "PASS" # Simulating check_data_gap_status
    results_data = load_json_safe(results_file)
    metrics_data = load_json_safe(metrics_file)
    permutation_data = load_json_safe(perm_file)
    threshold_data = load_json_safe(thresh_file)

    # Generate
    content = generate_research_report(
        data_gap_status,
        results_data,
        metrics_data,
        permutation_data,
        threshold_data
    )

    # Assertions
    assert "Data Gap Status" in content
    assert "Model Performance" in content or "ROC-AUC" in content
    assert "0.85" in content
    assert "Independent Validation" in content or "AUPRC" in content
    assert "0.78" in content
    assert "Feature Stability" in content or "Importance" in content
    assert "Threshold Sensitivity" in content
    assert "0.3" in content and "0.5" in content and "0.7" in content
    assert "DHW" in content
    assert "PASS" in content # For performance status

def test_generate_research_report_missing_data(tmp_path):
    """Test handling of missing input files."""
    import sys
    from types import ModuleType
    
    config_mock = ModuleType('config')
    config_mock.PROJECT_ROOT = str(tmp_path)
    sys.modules['config'] = config_mock

    from generate_research_report import generate_research_report

    # Call with None data
    content = generate_research_report(
        "FAIL",
        None,
        None,
        None,
        None
    )

    assert "Data sources were missing" in content
    assert "ROC-AUC results are missing" in content
    assert "AUPRC results are missing" in content
    assert "Feature importance and stability results are missing" in content
    assert "Threshold sensitivity results are missing" in content