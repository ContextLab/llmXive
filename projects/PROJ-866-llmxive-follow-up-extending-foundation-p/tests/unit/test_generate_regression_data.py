"""
Unit tests for generate_regression_data.py
"""
import json
import os
import tempfile
import csv
from pathlib import Path
import pytest
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.generate_regression_data import (
    load_processed_logs,
    calculate_error_rate,
    get_unique_reduction_pcts,
    bootstrap_confidence_interval,
    save_regression_data_to_csv
)

def create_mock_log(
    reduction_pct: float, 
    has_violation: bool = False, 
    depth: int = 5, 
    workflow_id: str = "test_1"
) -> dict:
    """Helper to create a mock execution log."""
    return {
        "workflow_id": workflow_id,
        "context_reduction_pct": reduction_pct,
        "is_valid": True,
        "status": "normal",
        "policy_violations": ["rule_A"] if has_violation else [],
        "violation_details": [{"node_id": "n1", "rule_id": "rule_A"}] if has_violation else [],
        "metadata": {
            "depth": depth,
            "complexity": 3
        }
    }

class TestLoadProcessedLogs:
    def test_load_valid_logs(self, tmp_path):
        """Test loading valid logs from directory."""
        # Create mock files
        log1 = create_mock_log(10.0, has_violation=False)
        log2 = create_mock_log(20.0, has_violation=True)
        
        with open(tmp_path / "log1.json", 'w') as f:
            json.dump(log1, f)
        with open(tmp_path / "log2.json", 'w') as f:
            json.dump(log2, f)
        
        logs = load_processed_logs(tmp_path)
        
        assert len(logs) == 2
        assert logs[0]["context_reduction_pct"] == 10.0
        assert logs[1]["policy_violations"] == ["rule_A"]

    def test_filter_invalid_logs(self, tmp_path):
        """Test that invalid logs are filtered out."""
        valid_log = create_mock_log(10.0, has_violation=False)
        invalid_log = create_mock_log(20.0, has_violation=True)
        invalid_log["is_valid"] = False
        
        with open(tmp_path / "valid.json", 'w') as f:
            json.dump(valid_log, f)
        with open(tmp_path / "invalid.json", 'w') as f:
            json.dump(invalid_log, f)
        
        logs = load_processed_logs(tmp_path, valid_only=True)
        
        assert len(logs) == 1
        assert logs[0]["workflow_id"] == "test_1"

class TestCalculateErrorRate:
    def test_zero_error_rate(self):
        """Test calculation when no violations exist."""
        logs = [
            create_mock_log(10.0, has_violation=False),
            create_mock_log(10.0, has_violation=False)
        ]
        rate, total, violations = calculate_error_rate(logs, 10.0)
        
        assert rate == 0.0
        assert total == 2
        assert violations == 0

    def test_nonzero_error_rate(self):
        """Test calculation with mixed violations."""
        logs = [
            create_mock_log(10.0, has_violation=True),
            create_mock_log(10.0, has_violation=False),
            create_mock_log(10.0, has_violation=True),
            create_mock_log(10.0, has_violation=False)
        ]
        rate, total, violations = calculate_error_rate(logs, 10.0)
        
        assert rate == 0.5
        assert total == 4
        assert violations == 2

    def test_no_matching_logs(self):
        """Test calculation when no logs match the percentage."""
        logs = [create_mock_log(20.0, has_violation=True)]
        rate, total, violations = calculate_error_rate(logs, 10.0)
        
        assert rate == 0.0
        assert total == 0
        assert violations == 0

class TestGetUniqueReductionPcts:
    def test_extract_unique_pcts(self):
        """Test extraction of unique reduction percentages."""
        logs = [
            create_mock_log(10.0),
            create_mock_log(20.0),
            create_mock_log(10.0),
            create_mock_log(30.0)
        ]
        pcts = get_unique_reduction_pcts(logs)
        
        assert pcts == [10.0, 20.0, 30.0]

    def test_ignore_deferred(self):
        """Test that [deferred] strings are ignored."""
        logs = [
            create_mock_log(10.0),
            {"context_reduction_pct": "[deferred]"}
        ]
        pcts = get_unique_reduction_pcts(logs)
        
        assert pcts == [10.0]

class TestBootstrapConfidenceInterval:
    def test_bootstrap_ci_narrow(self):
        """Test that CI is calculated correctly."""
        # Create a large dataset with known variance
        logs = [
            create_mock_log(10.0, has_violation=(i % 2 == 0))
            for i in range(100)
        ]
        
        ci_lower, ci_upper = bootstrap_confidence_interval(logs, 10.0, n_bootstrap=100, seed=42)
        
        assert ci_lower <= ci_upper
        assert 0.0 <= ci_lower <= 1.0
        assert 0.0 <= ci_upper <= 1.0

class TestSaveRegressionDataToCSV:
    def test_csv_structure(self, tmp_path):
        """Test that CSV is saved with correct columns."""
        logs = [
            create_mock_log(10.0, has_violation=True),
            create_mock_log(10.0, has_violation=False),
            create_mock_log(20.0, has_violation=False),
            create_mock_log(20.0, has_violation=False)
        ]
        
        output_file = tmp_path / "test_curve.csv"
        save_regression_data_to_csv(logs, output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 2
        assert set(rows[0].keys()) == {'reduction_pct', 'error_rate', 'depth', 'ci_lower', 'ci_upper'}
        
        # Check specific values
        row_10 = next(r for r in rows if float(r['reduction_pct']) == 10.0)
        assert float(row_10['error_rate']) == 0.5
        assert int(row_10['depth']) == 5