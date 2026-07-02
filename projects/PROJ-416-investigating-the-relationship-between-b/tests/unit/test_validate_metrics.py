"""
Unit tests for code/analysis/validate_metrics.py
"""
import pytest
import csv
import math
from pathlib import Path
import tempfile
import os

from code.analysis.validate_metrics import (
    load_metrics_from_csv,
    validate_metric_value,
    validate_metrics,
    run_validation
)
from code.config import Config

class TestLoadMetricsFromCsv:
    def test_load_valid_csv(self, tmp_path):
        """Test loading a valid CSV file."""
        csv_path = tmp_path / "test_metrics.csv"
        data = [
            {"subject_id": "S1", "modularity_q": "0.4", "global_efficiency": "0.6", "local_efficiency": "0.5"},
            {"subject_id": "S2", "modularity_q": "0.3", "global_efficiency": "0.7", "local_efficiency": "0.6"}
        ]
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        result = load_metrics_from_csv(csv_path)
        assert len(result) == 2
        assert result[0]['subject_id'] == 'S1'
        assert float(result[0]['modularity_q']) == 0.4

    def test_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_metrics_from_csv(tmp_path / "nonexistent.csv")

    def test_missing_columns(self, tmp_path):
        """Test that ValueError is raised for missing columns."""
        csv_path = tmp_path / "bad_metrics.csv"
        with open(csv_path, 'w', newline='') as f:
            f.write("subject_id,modularity_q\nS1,0.4\n")
        
        with pytest.raises(ValueError) as excinfo:
            load_metrics_from_csv(csv_path)
        assert "Missing required columns" in str(excinfo.value)

    def test_empty_file(self, tmp_path):
        """Test that ValueError is raised for empty file."""
        csv_path = tmp_path / "empty.csv"
        csv_path.touch()
        
        with pytest.raises(ValueError) as excinfo:
            load_metrics_from_csv(csv_path)
        assert "CSV file is empty" in str(excinfo.value) or "No data rows" in str(excinfo.value)

class TestValidateMetricValue:
    def test_valid_positive(self):
        """Test valid positive value."""
        assert validate_metric_value("0.5", "TestMetric", 0.0) == 0.5

    def test_valid_zero(self):
        """Test valid zero value."""
        assert validate_metric_value("0.0", "TestMetric", 0.0) == 0.0

    def test_invalid_negative(self):
        """Test that negative value below min raises error."""
        with pytest.raises(ValueError) as excinfo:
            validate_metric_value("-0.1", "TestMetric", 0.0)
        assert "below the minimum bound" in str(excinfo.value)

    def test_invalid_nan(self):
        """Test that NaN raises error."""
        with pytest.raises(ValueError) as excinfo:
            validate_metric_value("nan", "TestMetric", 0.0)
        assert "NaN" in str(excinfo.value)

    def test_invalid_inf(self):
        """Test that Infinity raises error."""
        with pytest.raises(ValueError) as excinfo:
            validate_metric_value("inf", "TestMetric", 0.0)
        assert "Infinity" in str(excinfo.value)

    def test_invalid_format(self):
        """Test that non-numeric string raises error."""
        with pytest.raises(ValueError) as excinfo:
            validate_metric_value("abc", "TestMetric", 0.0)
        assert "Invalid number format" in str(excinfo.value)

class TestValidateMetrics:
    def test_all_valid(self):
        """Test validation passes for valid data."""
        data = [
            {"subject_id": "S1", "modularity_q": "0.4", "global_efficiency": "0.6", "local_efficiency": "0.5"},
            {"subject_id": "S2", "modularity_q": "0.0", "global_efficiency": "0.0", "local_efficiency": "0.0"}
        ]
        assert validate_metrics(data) is True

    def test_one_invalid_modularity(self):
        """Test that validation fails for negative modularity."""
        data = [
            {"subject_id": "S1", "modularity_q": "0.4", "global_efficiency": "0.6", "local_efficiency": "0.5"},
            {"subject_id": "S2", "modularity_q": "-0.1", "global_efficiency": "0.6", "local_efficiency": "0.5"}
        ]
        with pytest.raises(SystemExit) as excinfo:
            validate_metrics(data)
        assert excinfo.value.code == 1

    def test_one_invalid_efficiency(self):
        """Test that validation fails for NaN efficiency."""
        data = [
            {"subject_id": "S1", "modularity_q": "0.4", "global_efficiency": "0.6", "local_efficiency": "0.5"},
            {"subject_id": "S2", "modularity_q": "0.3", "global_efficiency": "nan", "local_efficiency": "0.6"}
        ]
        with pytest.raises(SystemExit) as excinfo:
            validate_metrics(data)
        assert excinfo.value.code == 1

class TestRunValidation:
    def test_run_success(self, tmp_path, monkeypatch):
        """Test run_validation with a valid file."""
        # Create a mock config
        class MockConfig:
            METRICS_PATH = tmp_path
        
        csv_path = tmp_path / "network_metrics.csv"
        data = [
            {"subject_id": "S1", "modularity_q": "0.4", "global_efficiency": "0.6", "local_efficiency": "0.5"}
        ]
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        # Mock Config class to return our mock
        import code.analysis.validate_metrics as vm
        original_config = vm.Config
        vm.Config = MockConfig

        try:
            run_validation()
        finally:
            vm.Config = original_config

    def test_run_missing_file(self, tmp_path, monkeypatch):
        """Test run_validation when file is missing."""
        class MockConfig:
            METRICS_PATH = tmp_path / "nonexistent_dir"
        
        import code.analysis.validate_metrics as vm
        original_config = vm.Config
        vm.Config = MockConfig

        try:
            with pytest.raises(SystemExit) as excinfo:
                run_validation()
            assert excinfo.value.code == 1
        finally:
            vm.Config = original_config