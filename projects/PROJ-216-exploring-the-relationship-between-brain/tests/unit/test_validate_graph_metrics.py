"""
Unit tests for the graph metrics validation logic in validate_graph_metrics.py.
"""
import pytest
import os
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to test
# Note: Since validate_graph_metrics.py is in code/, we need to adjust sys.path or import relative to project root
# For unit tests, we will mock the file system interactions and test the logic directly.

# We will import the logic by temporarily adding the code directory to sys.path
import sys
project_root = Path(__file__).resolve().parent.parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from validate_graph_metrics import (
    validate_metric_value, 
    METRIC_RANGES,
    load_graph_metrics,
    write_anomalies
)


class TestValidateMetricValue:
    """Tests for the validate_metric_value function."""

    def test_valid_global_efficiency(self):
        is_valid, reason = validate_metric_value("global_efficiency", "0.5")
        assert is_valid is True
        assert reason == "OK"

    def test_boundary_low_global_efficiency(self):
        is_valid, reason = validate_metric_value("global_efficiency", "0.0")
        assert is_valid is True
        assert reason == "OK"

    def test_boundary_high_global_efficiency(self):
        is_valid, reason = validate_metric_value("global_efficiency", "1.0")
        assert is_valid is True
        assert reason == "OK"

    def test_invalid_low_global_efficiency(self):
        is_valid, reason = validate_metric_value("global_efficiency", "-0.1")
        assert is_valid is False
        assert "outside expected range" in reason

    def test_invalid_high_global_efficiency(self):
        is_valid, reason = validate_metric_value("global_efficiency", "1.1")
        assert is_valid is False
        assert "outside expected range" in reason

    def test_valid_clustering_coefficient(self):
        is_valid, reason = validate_metric_value("clustering_coefficient", "0.8")
        assert is_valid is True
        assert reason == "OK"

    def test_invalid_modularity(self):
        is_valid, reason = validate_metric_value("modularity", "1.5")
        assert is_valid is False
        assert "outside expected range" in reason

    def test_non_numeric_value(self):
        is_valid, reason = validate_metric_value("global_efficiency", "not_a_number")
        assert is_valid is False
        assert "Non-numeric value" in reason

    def test_unknown_metric(self):
        is_valid, reason = validate_metric_value("unknown_metric", "0.5")
        assert is_valid is True
        assert "has no defined range" in reason


class TestLoadGraphMetrics:
    """Tests for the load_graph_metrics function."""

    def test_load_valid_csv(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            writer = csv.DictWriter(f, fieldnames=["subject_id", "metric_name", "value"])
            writer.writeheader()
            writer.writerow({"subject_id": "sub-01", "metric_name": "global_efficiency", "value": "0.5"})
            writer.writerow({"subject_id": "sub-02", "metric_name": "clustering_coefficient", "value": "0.3"})
            temp_path = Path(f.name)

        try:
            metrics = load_graph_metrics(temp_path)
            assert len(metrics) == 2
            assert metrics[0]["subject_id"] == "sub-01"
            assert metrics[1]["metric_name"] == "clustering_coefficient"
        finally:
            temp_path.unlink()

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_graph_metrics(Path("/nonexistent/path/file.csv"))

    def test_empty_csv(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            writer = csv.DictWriter(f, fieldnames=["subject_id", "metric_name", "value"])
            writer.writeheader()
            temp_path = Path(f.name)

        try:
            metrics = load_graph_metrics(temp_path)
            assert len(metrics) == 0
        finally:
            temp_path.unlink()


class TestWriteAnomalies:
    """Tests for the write_anomalies function."""

    def test_write_anomalies(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "validation.log"
            anomalies = [
                "[sub-01] [global_efficiency] [1.5] [Value 1.5 outside expected range [0.0, 1.0]]",
                "[sub-02] [clustering_coefficient] [-0.1] [Value -0.1 outside expected range [0.0, 1.0]]"
            ]
            
            write_anomalies(anomalies, log_path)
            
            assert log_path.exists()
            with open(log_path, "r") as f:
                content = f.read()
                assert anomalies[0] in content
                assert anomalies[1] in content

    def test_write_empty_anomalies(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "validation.log"
            anomalies = []
            
            write_anomalies(anomalies, log_path)
            
            assert log_path.exists()
            with open(log_path, "r") as f:
                content = f.read()
                assert content == ""