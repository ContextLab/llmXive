"""
Tests for the Report Generator module (T012b).

Verifies that the final report correctly frames results as 'Validation-Only'
when synthetic fallback is triggered and 'Production Ready' for real data.
"""
import json
import os
import pytest
from pathlib import Path
from datetime import datetime

# Import the module under test
from code.report_generator import generate_final_report, save_final_report

class TestReportGeneration:
    """Test cases for report generation logic."""

    def test_real_data_framing(self):
        """Test that real data results are framed as 'Production Ready'."""
        report = generate_final_report(is_real_data=True)
        
        assert report["data_validity"]["is_real_data"] is True
        assert report["data_validity"]["fr_001_compliance"] is True
        assert report["data_validity"]["empirical_hypothesis_status"] == "Tested"
        assert report["result_framing"]["status"] == "Production Ready"
        assert len(report["result_framing"]["warning_flags"]) == 0

    def test_synthetic_fallback_framing(self):
        """Test that synthetic fallback results are framed as 'Validation-Only'."""
        report = generate_final_report(is_real_data=False)
        
        assert report["data_validity"]["is_real_data"] is False
        assert report["data_validity"]["fr_001_compliance"] is False
        assert report["data_validity"]["empirical_hypothesis_status"] == "Untested"
        assert report["result_framing"]["status"] == "Validation-Only"
        assert "SYNTHETIC_DATA_FALLBACK_ACTIVE" in report["result_framing"]["warning_flags"]
        assert "synthetic fallback" in report["result_framing"]["description"].lower()

    def test_report_metadata_structure(self):
        """Test that the report contains required metadata fields."""
        report = generate_final_report(is_real_data=True)
        
        assert "report_metadata" in report
        assert "generated_at" in report["report_metadata"]
        assert "pipeline_status" in report["report_metadata"]
        assert "data_source_type" in report["report_metadata"]
        
        # Verify data_source_type logic
        report_real = generate_final_report(is_real_data=True)
        report_synthetic = generate_final_report(is_real_data=False)
        
        assert report_real["report_metadata"]["data_source_type"] == "real"
        assert report_synthetic["report_metadata"]["data_source_type"] == "synthetic_fallback"

    def test_save_final_report_creates_file(self, tmp_path):
        """Test that save_final_report writes a valid JSON file."""
        report = generate_final_report(is_real_data=False)
        
        output_file = tmp_path / "test_report.json"
        saved_path = save_final_report(report, str(output_file))
        
        assert os.path.exists(saved_path)
        assert saved_path == str(output_file)
        
        with open(saved_path, 'r') as f:
            loaded_report = json.load(f)
        
        assert loaded_report == report

    def test_report_includes_optional_fields(self):
        """Test that optional metrics and model results are included when provided."""
        metrics = {"accuracy": 0.85, "roc_auc": 0.90}
        models = {"best_model": "xgboost"}
        
        report = generate_final_report(
            is_real_data=True,
            metrics_summary=metrics,
            model_results=models
        )
        
        assert "metrics_summary" in report
        assert report["metrics_summary"] == metrics
        assert "model_results" in report
        assert report["model_results"] == models

    def test_report_without_optional_fields(self):
        """Test that report works correctly without optional fields."""
        report = generate_final_report(is_real_data=True)
        
        assert "metrics_summary" not in report
        assert "model_results" not in report
