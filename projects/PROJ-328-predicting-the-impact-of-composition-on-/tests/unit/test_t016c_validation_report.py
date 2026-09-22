"""
Unit tests for T016c: Verify Validation Report Generation.

These tests verify that the generate_validation_report.py script:
1. Executes without errors when given valid mock inputs
2. Produces a valid YAML output file
3. The output file contains the expected schema and values
"""
import os
import sys
import json
import yaml
import tempfile
import shutil
from pathlib import Path
import pytest

# Ensure code/ is in path
code_root = Path(__file__).resolve().parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from ingestion.generate_validation_report import (
    load_ingestion_status,
    load_validation_metrics,
    generate_validation_report,
    save_report
)

class TestValidationReportGenerationUnit:
    """Unit tests for validation report generation functions."""

    @pytest.fixture(autouse=True)
    def setup_test_files(self):
        """Setup temporary files for testing."""
        self.temp_dir = tempfile.mkdtemp(prefix="test_t016c_")
        self.processed_dir = Path(self.temp_dir)
        
        # Create mock .ingestion_status.json
        self.status_file = self.processed_dir / ".ingestion_status.json"
        mock_status = {
            "threshold_status": "50<=N<100",
            "exact_N": 85,
            "excluded_count": 15,
            "power_limitation_warning": "Reduced statistical power due to N < 100"
        }
        with open(self.status_file, 'w') as f:
            json.dump(mock_status, f, indent=2)

        # Create mock validation_metrics.yaml
        self.metrics_file = self.processed_dir / "validation_metrics.yaml"
        mock_metrics = {
            "total_raw_records": 200,
            "passed_threshold_count": 185,
            "failed_threshold_count": 15,
            "pass_rate_percentage": 92.5
        }
        with open(self.metrics_file, 'w') as f:
            yaml.dump(mock_metrics, f, default_flow_style=False)

        yield

        # Cleanup
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_ingestion_status_success(self):
        """Test loading a valid ingestion status file."""
        status_data = load_ingestion_status(self.status_file)
        assert status_data["threshold_status"] == "50<=N<100"
        assert status_data["exact_N"] == 85
        assert status_data["excluded_count"] == 15
        assert status_data["power_limitation_warning"] == "Reduced statistical power due to N < 100"

    def test_load_ingestion_status_missing_file(self):
        """Test that loading a missing status file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_ingestion_status(self.processed_dir / "nonexistent.json")

    def test_load_validation_metrics_success(self):
        """Test loading a valid validation metrics file."""
        metrics_data = load_validation_metrics(self.metrics_file)
        assert metrics_data["total_raw_records"] == 200
        assert metrics_data["passed_threshold_count"] == 185
        assert metrics_data["failed_threshold_count"] == 15
        assert metrics_data["pass_rate_percentage"] == 92.5

    def test_load_validation_metrics_missing_file(self):
        """Test that loading a missing metrics file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_validation_metrics(self.processed_dir / "nonexistent.yaml")

    def test_generate_validation_report_transforms_data_correctly(self):
        """Test that the report generation correctly transforms input data."""
        status_data = load_ingestion_status(self.status_file)
        metrics_data = load_validation_metrics(self.metrics_file)
        
        report = generate_validation_report(status_data, metrics_data)
        
        assert report["status"] == "50<=N<100"
        assert report["count"] == 85
        assert report["excluded_count"] == 15
        assert report["pass_rate_percentage"] == 92.5
        assert report["total_raw_records"] == 200
        assert "power_limitation_warning" in report
        assert report["power_limitation_warning"] == "Reduced statistical power due to N < 100"

    def test_generate_validation_report_without_optional_fields(self):
        """Test report generation when optional fields are missing."""
        status_data = {
            "threshold_status": "N>=100",
            "exact_N": 120,
            "excluded_count": 5
        }
        metrics_data = {
            "total_raw_records": 125,
            "passed_threshold_count": 120,
            "failed_threshold_count": 5,
            "pass_rate_percentage": 96.0
        }
        
        report = generate_validation_report(status_data, metrics_data)
        
        assert report["status"] == "N>=100"
        assert report["count"] == 120
        assert report["excluded_count"] == 5
        assert report["pass_rate_percentage"] == 96.0
        assert "power_limitation_warning" not in report

    def test_save_report_creates_valid_yaml(self):
        """Test that saving the report creates a valid YAML file."""
        status_data = load_ingestion_status(self.status_file)
        metrics_data = load_validation_metrics(self.metrics_file)
        report_data = generate_validation_report(status_data, metrics_data)
        
        output_file = self.processed_dir / "test_report.yaml"
        save_report(report_data, output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            loaded_report = yaml.safe_load(f)
        
        assert loaded_report == report_data

    def test_save_report_creates_parent_directories(self):
        """Test that save_report creates parent directories if they don't exist."""
        status_data = load_ingestion_status(self.status_file)
        metrics_data = load_validation_metrics(self.metrics_file)
        report_data = generate_validation_report(status_data, metrics_data)
        
        output_file = self.processed_dir / "nested" / "dir" / "test_report.yaml"
        save_report(report_data, output_file)
        
        assert output_file.exists()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])