"""
Unit tests for T036: Validation Report Generation.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Mock the config to avoid path issues in tests
import sys
from io import StringIO

# We will test the logic by mocking the file I/O and config
# The actual script imports from code.config, so we need to ensure the test environment is set up
# or we test the functions directly with mocked paths.

from code.validation_report import (
    load_cv_results,
    load_sensitivity_results,
    generate_validation_report,
    run_validation_pipeline
)


class TestLoadCVResults:
    def test_load_cv_results_success(self, tmp_path):
        """Test successful loading of CV results."""
        test_data = {
            "mean_r2": 0.75,
            "std_r2": 0.03,
            "r2_scores": [0.72, 0.76, 0.74, 0.77, 0.75],
            "interaction_p_values": [0.01, 0.02, 0.015, 0.018, 0.012]
        }
        file_path = tmp_path / "cv_results.json"
        with open(file_path, 'w') as f:
            json.dump(test_data, f)

        result = load_cv_results(str(file_path))

        assert result['mean_r2'] == 0.75
        assert result['std_r2'] == 0.03
        assert 'r2_scores' in result

    def test_load_cv_results_missing_file(self, tmp_path):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            load_cv_results(str(tmp_path / "nonexistent.json"))

    def test_load_cv_results_missing_key(self, tmp_path):
        """Test error handling for missing required keys."""
        test_data = {"r2_scores": [0.7]} # Missing mean_r2
        file_path = tmp_path / "cv_results.json"
        with open(file_path, 'w') as f:
            json.dump(test_data, f)

        with pytest.raises(ValueError, match="Missing required key"):
            load_cv_results(str(file_path))


class TestLoadSensitivityResults:
    def test_load_sensitivity_results_success(self, tmp_path):
        """Test successful loading of sensitivity results."""
        test_data = {
            "step_sizes": [2, 5, 10],
            "p_values": [0.01, 0.012, 0.015],
            "variation_metrics": {
                "baseline_p_value": 0.01,
                "max_deviation_percent": 50.0,
                "threshold_exceeded": True
            }
        }
        file_path = tmp_path / "sensitivity_analysis.json"
        with open(file_path, 'w') as f:
            json.dump(test_data, f)

        result = load_sensitivity_results(str(file_path))

        assert result['variation_metrics']['max_deviation_percent'] == 50.0
        assert result['variation_metrics']['threshold_exceeded'] is True

    def test_load_sensitivity_results_missing_file(self, tmp_path):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            load_sensitivity_results(str(tmp_path / "nonexistent.json"))

    def test_load_sensitivity_results_missing_key(self, tmp_path):
        """Test error handling for missing required keys."""
        test_data = {"step_sizes": [2]} # Missing variation_metrics
        file_path = tmp_path / "sensitivity_analysis.json"
        with open(file_path, 'w') as f:
            json.dump(test_data, f)

        with pytest.raises(ValueError, match="Missing required key"):
            load_sensitivity_results(str(file_path))


class TestGenerateValidationReport:
    def test_generate_report_stable_model(self, tmp_path):
        """Test report generation for a stable model (low variance, low deviation)."""
        cv_data = {
            "mean_r2": 0.80,
            "std_r2": 0.02
        }
        sens_data = {
            "variation_metrics": {
                "baseline_p_value": 0.005,
                "max_deviation_percent": 10.0,
                "threshold_exceeded": False
            }
        }
        output_path = tmp_path / "report.md"

        generate_validation_report(cv_data, sens_data, str(output_path))

        assert output_path.exists()
        content = output_path.read_text()

        assert "Mean R² Score" in content
        assert "0.80" in content
        assert "0.02" in content
        assert "✅ **Pass**" in content
        assert "Robust generalizability" in content

    def test_generate_report_unstable_cv(self, tmp_path):
        """Test report generation for unstable CV."""
        cv_data = {
            "mean_r2": 0.50,
            "std_r2": 0.20 # High variance
        }
        sens_data = {
            "variation_metrics": {
                "baseline_p_value": 0.01,
                "max_deviation_percent": 5.0,
                "threshold_exceeded": False
            }
        }
        output_path = tmp_path / "report.md"

        generate_validation_report(cv_data, sens_data, str(output_path))

        content = output_path.read_text()
        assert "Unstable" in content
        assert "high variance" in content

    def test_generate_report_sensitive_pvalue(self, tmp_path):
        """Test report generation for sensitive p-value."""
        cv_data = {
            "mean_r2": 0.75,
            "std_r2": 0.03
        }
        sens_data = {
            "variation_metrics": {
                "baseline_p_value": 0.01,
                "max_deviation_percent": 150.0,
                "threshold_exceeded": True
            }
        }
        output_path = tmp_path / "report.md"

        generate_validation_report(cv_data, sens_data, str(output_path))

        content = output_path.read_text()
        assert "⚠️ **Warning**" in content
        assert "sensitive to Sholl radius" in content


def test_run_validation_pipeline_integration(tmp_path, monkeypatch):
    """Integration test for the full pipeline using mocked config and file system."""
    # Create temporary files for inputs
    cv_file = tmp_path / "data" / "intermediates" / "cv_results.json"
    sens_file = tmp_path / "data" / "intermediates" / "sensitivity_analysis.json"
    output_file = tmp_path / "reports" / "validation_report.md"

    for f in [cv_file, sens_file]:
        f.parent.mkdir(parents=True, exist_ok=True)

    cv_data = {"mean_r2": 0.70, "std_r2": 0.04}
    sens_data = {"variation_metrics": {"baseline_p_value": 0.02, "max_deviation_percent": 20.0, "threshold_exceeded": False}}

    with open(cv_file, 'w') as f:
        json.dump(cv_data, f)
    with open(sens_file, 'w') as f:
        json.dump(sens_data, f)

    # Mock get_path to use our tmp_path
    import code.validation_report as vr_module
    original_get_path = vr_module.get_path
    original_get_project_root = vr_module.get_project_root

    def mock_get_path(root, rel):
        return str(tmp_path / rel)

    def mock_get_root():
        return tmp_path

    monkeypatch.setattr(vr_module, 'get_path', mock_get_path)
    monkeypatch.setattr(vr_module, 'get_project_root', mock_get_root)

    try:
        result_path = run_validation_pipeline()
        assert result_path == str(output_file)
        assert output_file.exists()
        assert "Validation Report" in output_file.read_text()
    finally:
        # Restore
        vr_module.get_path = original_get_path
        vr_module.get_project_root = original_get_project_root