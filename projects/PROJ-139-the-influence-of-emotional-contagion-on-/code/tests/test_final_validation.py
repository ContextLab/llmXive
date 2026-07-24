"""
Unit tests for the final validation module (T039).
"""

import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# We need to import the functions from the module.
# Since the module uses absolute paths based on __file__, we need to be careful.
# For testing, we will mock the file system interactions.

import sys
from pathlib import Path

# Add the project root to the path to allow imports
# Assuming this test is in code/tests/
# The module is in code/analysis/final_validation.py
# So we need to add code/ to the path
code_path = Path(__file__).parent.parent
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from analysis.final_validation import (
    check_sc_001_variable_fit,
    check_sc_002_associational_framing,
    check_sc_003_multiple_comparison,
    check_sc_004_threshold_sensitivity,
    check_sc_005_performance,
    check_sc_006_ground_truth,
    run_final_validation
)


@pytest.fixture
def mock_project_structure(tmp_path):
    """Create a mock project structure with necessary files."""
    # Create directories
    data_processed = tmp_path / "data" / "processed"
    state_dir = tmp_path / "state"
    docs_dir = tmp_path / "docs"
    data_processed.mkdir(parents=True)
    state_dir.mkdir(parents=True)
    docs_dir.mkdir(parents=True)

    # Create mock files
    # thread_metrics.csv
    metrics_df = pd.DataFrame({
        "thread_id": [1, 2, 3],
        "contagion_index": [0.1, 0.2, 0.3]
    })
    metrics_df.to_csv(data_processed / "thread_metrics.csv", index=False)

    # valid_threads.csv
    valid_df = pd.DataFrame({
        "thread_id": [1, 2, 3],
        "agreement_proportion": [0.8, 0.9, 0.7],
        "shannon_entropy": [0.2, 0.1, 0.3],
        "external_validation_score": [0.9, 0.85, 0.95]
    })
    valid_df.to_csv(data_processed / "valid_threads.csv", index=False)

    # sensitivity_analysis.csv
    sens_df = pd.DataFrame({
        "agreement_cutoff": [0.5, 0.6, 0.7],
        "entropy_threshold": [0.2, 0.4, 0.6],
        "trend_summary": ["stable", "stable", "stable"]
    })
    sens_df.to_csv(data_processed / "sensitivity_analysis.csv", index=False)

    # validity_status.json
    validity_data = {
        "sc_006_compliance": True,
        "status": "pass",
        "valid_thread_percentage": 45.0
    }
    with open(state_dir / "validity_status.json", 'w') as f:
        json.dump(validity_data, f)

    # performance_log.json
    perf_data = {
        "total_runtime_seconds": 3000,
        "thread_count": 100,
        "status": "success",
        "resource_check": {"cpu": True, "ram_gb": 4.0, "disk_gb": 10.0}
    }
    with open(state_dir / "performance_log.json", 'w') as f:
        json.dump(perf_data, f)

    # paper.md
    paper_content = """
    # Research Paper

    ## Methodology
    This study is observational. All reported relationships are correlational and should not be interpreted as causal.

    ## Results
    We applied Bonferroni correction for multiple comparisons.
    """
    with open(docs_dir / "paper.md", 'w') as f:
        f.write(paper_content)

    return tmp_path


def test_check_sc_001_variable_fit_success(mock_project_structure):
    with patch('analysis.final_validation.PROJECT_ROOT', mock_project_structure):
        result = check_sc_001_variable_fit()
        assert result["status"] == "pass"
        assert "All required variables fit criteria" in result["details"]


def test_check_sc_001_variable_fit_missing_file(mock_project_structure):
    # Remove thread_metrics.csv
    (mock_project_structure / "data" / "processed" / "thread_metrics.csv").unlink()

    with patch('analysis.final_validation.PROJECT_ROOT', mock_project_structure):
        result = check_sc_001_variable_fit()
        assert result["status"] == "fail"
        assert "Missing file" in result["details"][0]


def test_check_sc_002_associational_framing_success(mock_project_structure):
    with patch('analysis.final_validation.PROJECT_ROOT', mock_project_structure):
        result = check_sc_002_associational_framing()
        assert result["status"] == "pass"


def test_check_sc_002_associational_framing_fail(mock_project_structure):
    # Remove paper.md
    (mock_project_structure / "docs" / "paper.md").unlink()
    with patch('analysis.final_validation.PROJECT_ROOT', mock_project_structure):
        result = check_sc_002_associational_framing()
        assert result["status"] == "fail"


def test_check_sc_003_multiple_comparison_success(mock_project_structure):
    with patch('analysis.final_validation.PROJECT_ROOT', mock_project_structure):
        result = check_sc_003_multiple_comparison()
        assert result["status"] == "pass"


def test_check_sc_004_threshold_sensitivity_success(mock_project_structure):
    with patch('analysis.final_validation.PROJECT_ROOT', mock_project_structure):
        result = check_sc_004_threshold_sensitivity()
        assert result["status"] == "pass"


def test_check_sc_005_performance_success(mock_project_structure):
    with patch('analysis.final_validation.PROJECT_ROOT', mock_project_structure):
        result = check_sc_005_performance()
        assert result["status"] == "pass"


def test_check_sc_005_performance_timeout(mock_project_structure):
    # Modify performance_log to exceed time
    perf_data = {
        "total_runtime_seconds": 6 * 60 * 60 + 1,
        "status": "success"
    }
    with open(mock_project_structure / "state" / "performance_log.json", 'w') as f:
        json.dump(perf_data, f)

    with patch('analysis.final_validation.PROJECT_ROOT', mock_project_structure):
        result = check_sc_005_performance()
        assert result["status"] == "fail"


def test_check_sc_006_ground_truth_success(mock_project_structure):
    with patch('analysis.final_validation.PROJECT_ROOT', mock_project_structure):
        result = check_sc_006_ground_truth()
        assert result["status"] == "pass"


def test_check_sc_006_ground_truth_fail(mock_project_structure):
    # Modify validity_status to fail
    validity_data = {
        "sc_006_compliance": False,
        "status": "fail"
    }
    with open(mock_project_structure / "state" / "validity_status.json", 'w') as f:
        json.dump(validity_data, f)

    with patch('analysis.final_validation.PROJECT_ROOT', mock_project_structure):
        result = check_sc_006_ground_truth()
        assert result["status"] == "fail"


def test_run_final_validation_success(mock_project_structure):
    with patch('analysis.final_validation.PROJECT_ROOT', mock_project_structure):
        success, results = run_final_validation()
        assert success is True
        assert all(r["status"] == "pass" for r in results.values())


def test_run_final_validation_partial_fail(mock_project_structure):
    # Make SC-005 fail
    perf_data = {
        "total_runtime_seconds": 6 * 60 * 60 + 1,
        "status": "success"
    }
    with open(mock_project_structure / "state" / "performance_log.json", 'w') as f:
        json.dump(perf_data, f)

    with patch('analysis.final_validation.PROJECT_ROOT', mock_project_structure):
        success, results = run_final_validation()
        assert success is False
        assert results["sc_005"]["status"] == "fail"
        assert results["sc_001"]["status"] == "pass"  # Others should pass