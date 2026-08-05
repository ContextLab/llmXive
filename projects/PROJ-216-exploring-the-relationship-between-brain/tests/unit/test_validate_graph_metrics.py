import os
import sys
import csv
import tempfile
from pathlib import Path
import pytest

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.validate_graph_metrics import (
    load_graph_metrics,
    validate_metric_value,
    write_anomalies,
    VALID_RANGES
)

class TestValidateGraphMetrics:
    
    def test_validate_metric_value_efficiency_valid(self):
        """Test valid efficiency value (0-1)"""
        is_valid, reason = validate_metric_value("sub-001", "global_efficiency", "0.5")
        assert is_valid is True
        assert reason == ""

    def test_validate_metric_value_efficiency_too_low(self):
        """Test efficiency value below 0"""
        is_valid, reason = validate_metric_value("sub-001", "global_efficiency", "-0.1")
        assert is_valid is False
        assert "below minimum" in reason

    def test_validate_metric_value_efficiency_too_high(self):
        """Test efficiency value above 1"""
        is_valid, reason = validate_metric_value("sub-001", "global_efficiency", "1.5")
        assert is_valid is False
        assert "exceeds maximum" in reason

    def test_validate_metric_value_non_numeric(self):
        """Test non-numeric value"""
        is_valid, reason = validate_metric_value("sub-001", "global_efficiency", "abc")
        assert is_valid is False
        assert "not a valid number" in reason

    def test_validate_metric_value_clustering_coefficient(self):
        """Test clustering coefficient range"""
        is_valid, _ = validate_metric_value("sub-001", "clustering_coefficient", "0.8")
        assert is_valid is True

        is_valid, reason = validate_metric_value("sub-001", "clustering_coefficient", "1.2")
        assert is_valid is False

    def test_validate_metric_value_path_length(self):
        """Test path length (positive only)"""
        is_valid, _ = validate_metric_value("sub-001", "characteristic_path_length", "5.0")
        assert is_valid is True

        is_valid, reason = validate_metric_value("sub-001", "characteristic_path_length", "-2.0")
        assert is_valid is False

    def test_write_anomalies_format(self, tmp_path):
        """Test that anomalies are written in correct format"""
        anomalies = [
            ("sub-001", "global_efficiency", "-0.5", "REASON: Value -0.5 is below minimum 0.0"),
            ("sub-002", "modularity", "1.5", "REASON: Value 1.5 exceeds maximum 1.0")
        ]
        
        log_path = tmp_path / "test_validation.log"
        write_anomalies(anomalies, str(log_path))
        
        assert log_path.exists()
        content = log_path.read_text()
        
        # Check format: [SUBJECT_ID] [METRIC] [VALUE] [REASON]
        lines = content.strip().split("\n")
        assert len(lines) == 2
        assert lines[0].startswith("[sub-001] [global_efficiency] [-0.5] [")
        assert lines[1].startswith("[sub-002] [modularity] [1.5] [")

    def test_load_graph_metrics(self, tmp_path):
        """Test loading metrics from CSV"""
        csv_path = tmp_path / "metrics.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["subject_id", "metric_name", "value"])
            writer.writeheader()
            writer.writerow({"subject_id": "sub-001", "metric_name": "global_efficiency", "value": "0.5"})
            writer.writerow({"subject_id": "sub-002", "metric_name": "modularity", "value": "0.3"})
        
        metrics = load_graph_metrics(str(csv_path))
        assert len(metrics) == 2
        assert metrics[0]["subject_id"] == "sub-001"
        assert metrics[1]["metric_name"] == "modularity"

    def test_load_graph_metrics_file_not_found(self):
        """Test error handling for missing file"""
        with pytest.raises(FileNotFoundError):
            load_graph_metrics("nonexistent/path/metrics.csv")
