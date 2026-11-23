"""
Unit tests for the final report generation module (T045).

These tests verify that the report generator correctly synthesizes
causal and sensitivity data into the required JSON structure,
adhering to FR-001 through FR-009.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.reporting.generate_final_report import (
    generate_final_report,
    generate_causal_section,
    generate_sensitivity_section,
    generate_limitations_section,
    generate_reproducibility_section,
    load_sensitivity_data
)
from src.models.output import AnalysisResult

@pytest.fixture
def mock_analysis_result():
    """Fixture providing a mock AnalysisResult dictionary."""
    return {
        "att": -150.50,
        "standard_error": 25.30,
        "p_value": 0.001,
        "confidence_interval": [-200.0, -101.0],
        "methodology": "PSM-OLS",
        "cluster_robust_se": True,
        "placebo_passed": True,
        "placebo_p_value": 0.45,
        "max_smd": 0.08,
        "caliper": 0.05,
        "balance_status": "PASS"
    }

@pytest.fixture
def mock_sensitivity_data():
    """Fixture providing mock sensitivity sweep data."""
    return {
        "caliper_sweep": [
            {"caliper": 0.01, "att": -148.0, "p_value": 0.002},
            {"caliper": 0.05, "att": -150.5, "p_value": 0.001},
            {"caliper": 0.10, "att": -152.0, "p_value": 0.003}
        ],
        "status": "success"
    }

def test_generate_causal_section_structure(mock_analysis_result):
    """Test that the causal section contains all required FR fields."""
    section = generate_causal_section(mock_analysis_result)

    assert "primary_estimate" in section
    assert "att" in section["primary_estimate"]
    assert "p_value" in section["primary_estimate"]
    assert "confidence_interval_95" in section["primary_estimate"]
    assert "methodology" in section["primary_estimate"]

    assert "placebo_test" in section
    assert "passed" in section["placebo_test"]
    assert "p_value" in section["placebo_test"]

    assert "balance_metrics" in section
    assert "max_smd" in section["balance_metrics"]
    assert "status" in section["balance_metrics"]

def test_generate_sensitivity_section_structure(mock_sensitivity_data):
    """Test that the sensitivity section correctly formats sweep data."""
    section = generate_sensitivity_section(mock_sensitivity_data)

    assert "description" in section
    assert "results" in section
    assert len(section["results"]) == 3
    assert "stability_assessment" in section
    assert "recommendation" in section

def test_generate_limitations_section(mock_analysis_result):
    """Test that limitations section documents assumptions."""
    section = generate_limitations_section(mock_analysis_result)

    assert "unconfoundedness" in section
    assert "overlap" in section
    assert "data_quality" in section
    assert "balance_status" in section

def test_generate_reproducibility_section():
    """Test that reproducibility section includes timestamp and seeds."""
    section = generate_reproducibility_section()

    assert "timestamp" in section
    assert "python_version" in section
    assert "seeds" in section
    assert "data_version" in section

def test_generate_final_report_integration(mock_analysis_result, mock_sensitivity_data):
    """Test end-to-end report generation with temporary files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        result_file = tmp_path / "analysis_result.json"
        sens_file = tmp_path / "sensitivity_analysis.json"
        report_file = tmp_path / "final_report.json"

        # Write mock data
        with open(result_file, "w") as f:
            json.dump(mock_analysis_result, f)
        with open(sens_file, "w") as f:
            json.dump(mock_sensitivity_data, f)

        # Generate report
        output_path = generate_final_report(
            analysis_result_path=str(result_file),
            sensitivity_path=str(sens_file),
            output_path=str(report_file)
        )

        # Verify file exists
        assert output_path.exists()

        # Verify JSON structure
        with open(output_path, "r") as f:
            report = json.load(f)

        assert "metadata" in report
        assert "causal_inference" in report
        assert "sensitivity_analysis" in report
        assert "limitations" in report
        assert "functional_requirements_adherence" in report

        # Verify FR-001 to FR-009 keys
        fr_keys = report["functional_requirements_adherence"]
        for i in range(1, 10):
            assert f"FR-{i:02d}" in fr_keys

def test_generate_final_report_missing_sensitivity(mock_analysis_result):
    """Test report generation when sensitivity data is missing (should warn)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        result_file = tmp_path / "analysis_result.json"
        report_file = tmp_path / "final_report.json"

        with open(result_file, "w") as f:
            json.dump(mock_analysis_result, f)

        # Sensitivity file does not exist
        output_path = generate_final_report(
            analysis_result_path=str(result_file),
            sensitivity_path=str(tmp_path / "nonexistent.json"),
            output_path=str(report_file)
        )

        assert output_path.exists()
        with open(output_path, "r") as f:
            report = json.load(f)

        # Should contain empty/missing sensitivity data
        assert report["sensitivity_analysis"]["status"] == "missing"

def test_generate_final_report_missing_analysis_result():
    """Test that report generation fails loudly if analysis result is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(FileNotFoundError):
            generate_final_report(
                analysis_result_path=str(Path(tmpdir) / "missing.json"),
                output_path=str(Path(tmpdir) / "report.json")
            )