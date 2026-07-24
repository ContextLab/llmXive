"""
Tests for the final report generation module (T038).
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# Import the module functions
# Note: We need to ensure the path is correct. Assuming code/analysis/generate_final_reports.py
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.generate_final_reports import (
    load_json,
    load_csv,
    generate_paper_content,
    generate_summary_content,
    main
)


class TestLoaders:
    def test_load_json_success(self, tmp_path):
        data = {"key": "value", "num": 123}
        file_path = tmp_path / "test.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        result = load_json(file_path)
        assert result == data

    def test_load_json_missing(self, tmp_path):
        result = load_json(tmp_path / "nonexistent.json")
        assert result is None

    def test_load_csv_success(self, tmp_path):
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        file_path = tmp_path / "test.csv"
        df.to_csv(file_path, index=False)
        
        result = load_csv(file_path)
        assert result.equals(df)

    def test_load_csv_missing(self, tmp_path):
        result = load_csv(tmp_path / "nonexistent.csv")
        assert result is None


class TestReportGeneration:
    def test_generate_paper_content_basic(self):
        # Minimal valid inputs
        validity_status = {"status": "pass", "valid_thread_percentage": 50.0, "sc_006_compliance": True}
        thread_metrics = pd.DataFrame({"contagion_index": [0.5, 0.6]})
        decision_quality = pd.DataFrame({"agreement_proportion": [0.8], "shannon_entropy": [0.2]})
        sensitivity_analysis = pd.DataFrame({
            "agreement_cutoff": [0.5], 
            "entropy_threshold": [0.2], 
            "correlation_agreement": [0.1], 
            "correlation_entropy": [0.2], 
            "trend_summary": ["stable"]
        })
        external_validation_corr = pd.DataFrame({"metric": ["test"], "correlation": [0.5], "p_value": [0.01]})
        collinearity = {"vif_scores": {"sentiment": 1.2}, "flagged": False}
        performance = {"total_runtime_seconds": 100, "status": "success", "thread_count": 200}
        validation_summary = {"sc_004_compliance": True}
        final_validation = {"all_criteria_met": True, "details": {"sc_001": True}}
        model_results = {"glmm_coefficients": [{"name": "sentiment", "estimate": 0.5, "std_err": 0.1, "p_value": 0.001}]}

        content = generate_paper_content(
            validity_status, thread_metrics, decision_quality, sensitivity_analysis,
            external_validation_corr, collinearity, performance, validation_summary,
            final_validation, model_results
        )

        assert "## Abstract" in content
        assert "## 1. Introduction" in content
        assert "## 3. Results" in content
        assert "SC-006" in content
        assert "50.00%" in content
        assert "Mean Contagion Index" in content
        assert "0.5500" in content # Mean of 0.5 and 0.6
        assert "GLMM coefficients" in content

    def test_generate_summary_content_power_limitation(self):
        validity_status = {"sc_006_compliance": True}
        performance = {"total_runtime_seconds": 100, "thread_count": 50} # < 100
        validation_summary = {"sc_004_compliance": True}
        final_validation = {"all_criteria_met": True}
        collinearity = None

        content = generate_summary_content(
            validity_status, performance, validation_summary, final_validation, collinearity
        )

        assert "Power limitation detected" in content
        assert "n = 50" in content

    def test_generate_summary_content_no_power_limitation(self):
        validity_status = {"sc_006_compliance": True}
        performance = {"total_runtime_seconds": 100, "thread_count": 150} # >= 100
        validation_summary = {"sc_004_compliance": True}
        final_validation = {"all_criteria_met": True}
        collinearity = None

        content = generate_summary_content(
            validity_status, performance, validation_summary, final_validation, collinearity
        )

        assert "Power Status" in content
        assert "Sufficient" in content
        assert "Power limitation" not in content

@pytest.fixture
def mock_paths(self, tmp_path):
    # Create a temporary directory structure mimicking the project
    data_processed = tmp_path / "data" / "processed"
    data_processed.mkdir(parents=True)
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    # Create dummy files
    (data_processed / "validity_status.json").write_text('{"status": "pass", "valid_thread_percentage": 50.0, "sc_006_compliance": true}')
    pd.DataFrame({"contagion_index": [0.1, 0.2]}).to_csv(data_processed / "thread_metrics.csv", index=False)
    pd.DataFrame({"agreement_proportion": [0.5], "shannon_entropy": [0.3]}).to_csv(data_processed / "decision_quality_metrics.csv", index=False)
    pd.DataFrame({"agreement_cutoff": [0.5], "entropy_threshold": [0.2], "correlation_agreement": [0.1], "correlation_entropy": [0.1], "trend_summary": ["stable"]}).to_csv(data_processed / "sensitivity_analysis.csv", index=False)
    pd.DataFrame({"metric": ["test"], "correlation": [0.1], "p_value": [0.5]}).to_csv(data_processed / "external_validation_correlation.csv", index=False)
    json.dump({"vif_scores": {"sentiment": 1.0}, "flagged": False}, open(data_processed / "collinearity_diagnostics.json", 'w'))
    json.dump({"total_runtime_seconds": 100, "status": "success", "thread_count": 100}, open(state_dir / "performance_log.json", 'w'))
    json.dump({"sc_004_compliance": True}, open(state_dir / "validation_summary.json", 'w'))
    json.dump({"all_criteria_met": True, "details": {"sc_001": True}}, open(state_dir / "final_validation.json", 'w'))
    json.dump({"glmm_coefficients": []}, open(data_processed / "model_results.json", 'w'))

    return tmp_path

def test_main_integration(self, mock_paths, tmp_path, monkeypatch):
    # Mock the global paths in the module to point to our temp directory
    from analysis import generate_final_reports
    monkeypatch.setattr(generate_final_reports, 'PROJECT_ROOT', mock_paths)
    monkeypatch.setattr(generate_final_reports, 'DATA_PROCESSED', mock_paths / "data" / "processed")
    monkeypatch.setattr(generate_final_reports, 'STATE_DIR', mock_paths / "state")
    monkeypatch.setattr(generate_final_reports, 'DOCS_DIR', mock_paths / "docs")

    # Run main
    main()

    # Check outputs
    assert (mock_paths / "docs" / "paper.md").exists()
    assert (mock_paths / "docs" / "analysis_summary.md").exists()