"""
Unit tests for T016c verification logic.
"""
import os
import sys
import json
import yaml
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ingestion.generate_validation_report import (
    load_ingestion_status,
    load_validation_metrics,
    generate_validation_report,
    save_report
)

class TestValidationReportGeneration:
    """Tests for the validation report generation logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.status_file = self.temp_dir / ".ingestion_status.json"
        self.metrics_file = self.temp_dir / "validation_metrics.yaml"
        self.report_file = self.temp_dir / "validation_report.yaml"

        # Mock data
        self.mock_status = {
            "threshold_status": "50<=N<100",
            "exact_N": 78,
            "excluded_count": 12,
            "power_limitation_warning": "N < 100: Statistical power may be limited."
        }

        self.mock_metrics = {
            "total_raw_records": 90,
            "passed_threshold_count": 78,
            "failed_threshold_count": 12,
            "pass_rate_percentage": 86.67
        }

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_ingestion_status_success(self):
        """Test loading a valid ingestion status JSON file."""
        with open(self.status_file, 'w') as f:
            json.dump(self.mock_status, f)

        result = load_ingestion_status(self.status_file)
        assert result is not None
        assert result["threshold_status"] == "50<=N<100"
        assert result["exact_N"] == 78

    def test_load_ingestion_status_not_found(self):
        """Test loading a non-existent ingestion status file."""
        result = load_ingestion_status(self.temp_dir / "nonexistent.json")
        assert result is None

    def test_load_validation_metrics_success(self):
        """Test loading a valid validation metrics YAML file."""
        with open(self.metrics_file, 'w') as f:
            yaml.dump(self.mock_metrics, f)

        result = load_validation_metrics(self.metrics_file)
        assert result is not None
        assert result["total_raw_records"] == 90
        assert result["pass_rate_percentage"] == 86.67

    def test_load_validation_metrics_not_found(self):
        """Test loading a non-existent validation metrics file."""
        result = load_validation_metrics(self.temp_dir / "nonexistent.yaml")
        assert result is None

    def test_generate_validation_report_structure(self):
        """Test that the generated report has the correct structure."""
        report = generate_validation_report(self.mock_status, self.mock_metrics)

        assert "status" in report
        assert "count" in report
        assert "excluded_count" in report
        assert "pass_rate_percentage" in report
        assert "power_limitation_warning" in report

        assert report["status"] == "50<=N<100"
        assert report["count"] == 78
        assert report["excluded_count"] == 12
        assert report["pass_rate_percentage"] == 86.67
        assert report["power_limitation_warning"] == "N < 100: Statistical power may be limited."

    def test_generate_validation_report_missing_optional(self):
        """Test report generation when optional fields are missing."""
        minimal_status = {
            "threshold_status": "N>=100",
            "exact_N": 150,
            "excluded_count": 5
        }
        
        report = generate_validation_report(minimal_status, self.mock_metrics)

        assert "status" in report
        assert "count" in report
        assert "excluded_count" in report
        assert "pass_rate_percentage" in report
        # power_limitation_warning should not be present if not in status
        assert "power_limitation_warning" not in report

    def test_save_report(self):
        """Test saving the report to a YAML file."""
        report = generate_validation_report(self.mock_status, self.mock_metrics)
        success = save_report(report, self.report_file)

        assert success is True
        assert self.report_file.exists()

        # Verify content
        with open(self.report_file, 'r') as f:
            loaded_report = yaml.safe_load(f)

        assert loaded_report == report
