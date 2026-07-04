"""
Unit tests for the export validator (T060).
Verifies that the export_validator module correctly detects inconsistencies
between the JSON audit report and the CSV summary report.
"""

import json
import csv
import os
import tempfile
import pytest
from pathlib import Path

# Import the module under test
from code.src.audit.export_validator import (
    load_audit_records_from_json,
    load_summary_counts_from_csv,
    validate_export_consistency,
)

# Helper fixtures for test data
def create_valid_audit_json(tmp_path: Path):
    """Creates a valid audit_report.json with consistent counts."""
    data = [
        {
            "url": "https://example.com/test1",
            "is_inconsistent": False,
            "p_value_reported": 0.03,
            "p_value_reconstructed": 0.031,
            "domain": "tech"
        },
        {
            "url": "https://example.com/test2",
            "is_inconsistent": True,
            "p_value_reported": 0.01,
            "p_value_reconstructed": 0.08,
            "domain": "finance"
        },
        {
            "url": "https://example.com/test3",
            "is_inconsistent": True,
            "p_value_reported": 0.04,
            "p_value_reconstructed": 0.09,
            "domain": "healthcare"
        }
    ]
    file_path = tmp_path / "audit_report.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return file_path

def create_valid_summary_csv(tmp_path: Path, inconsistent_count: int, total_count: int):
    """Creates a summary_report.csv with specific counts."""
    file_path = tmp_path / "summary_report.csv"
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "total_summaries", "inconsistent_count", "inconsistent_rate",
            "bias_adjusted_rate", "wilson_ci_lower", "wilson_ci_upper"
        ])
        writer.writeheader()
        writer.writerow({
            "total_summaries": total_count,
            "inconsistent_count": inconsistent_count,
            "inconsistent_rate": inconsistent_count / total_count if total_count > 0 else 0.0,
            "bias_adjusted_rate": 0.0,
            "wilson_ci_lower": 0.0,
            "wilson_ci_upper": 0.0
        })
    return file_path

class TestExportValidator:
    """Tests for export_validator consistency checks."""

    def test_load_audit_records_from_json_valid(self, tmp_path):
        """Test loading a valid JSON file."""
        json_path = create_valid_audit_json(tmp_path)
        records = load_audit_records_from_json(json_path)
        
        assert len(records) == 3
        assert records[0]["is_inconsistent"] is False
        assert records[1]["is_inconsistent"] is True

    def test_load_audit_records_from_json_missing_file(self, tmp_path):
        """Test handling of missing JSON file."""
        non_existent = tmp_path / "non_existent.json"
        with pytest.raises(FileNotFoundError):
            load_audit_records_from_json(non_existent)

    def test_load_summary_counts_from_csv_valid(self, tmp_path):
        """Test loading counts from a valid CSV."""
        csv_path = create_valid_summary_csv(tmp_path, inconsistent_count=2, total_count=3)
        counts = load_summary_counts_from_csv(csv_path)
        
        assert counts["total_summaries"] == 3
        assert counts["inconsistent_count"] == 2

    def test_load_summary_counts_from_csv_missing_file(self, tmp_path):
        """Test handling of missing CSV file."""
        non_existent = tmp_path / "non_existent.csv"
        with pytest.raises(FileNotFoundError):
            load_summary_counts_from_csv(non_existent)

    def test_validate_export_consistency_passes(self, tmp_path):
        """Test that validation passes when counts match."""
        json_path = create_valid_audit_json(tmp_path) # 3 total, 2 inconsistent
        csv_path = create_valid_summary_csv(tmp_path, inconsistent_count=2, total_count=3)
        
        is_consistent, error_msg = validate_export_consistency(json_path, csv_path)
        
        assert is_consistent is True
        assert error_msg is None

    def test_validate_export_consistency_mismatch_inconsistent_count(self, tmp_path):
        """Test that validation catches mismatch in inconsistent_count (T060 requirement)."""
        # JSON has 2 inconsistent, CSV claims 1
        json_path = create_valid_audit_json(tmp_path) 
        csv_path = create_valid_summary_csv(tmp_path, inconsistent_count=1, total_count=3)
        
        is_consistent, error_msg = validate_export_consistency(json_path, csv_path)
        
        assert is_consistent is False
        assert "inconsistent_count" in error_msg
        assert "1" in error_msg and "2" in error_msg

    def test_validate_export_consistency_mismatch_total_count(self, tmp_path):
        """Test that validation catches mismatch in total_count."""
        # JSON has 3 total, CSV claims 5
        json_path = create_valid_audit_json(tmp_path)
        csv_path = create_valid_summary_csv(tmp_path, inconsistent_count=2, total_count=5)
        
        is_consistent, error_msg = validate_export_consistency(json_path, csv_path)
        
        assert is_consistent is False
        assert "total_summaries" in error_msg
        assert "5" in error_msg and "3" in error_msg

    def test_validate_export_consistency_malformed_json(self, tmp_path):
        """Test handling of malformed JSON."""
        json_path = tmp_path / "malformed.json"
        with open(json_path, "w") as f:
            f.write("{ this is not valid json }")
        
        csv_path = create_valid_summary_csv(tmp_path, 0, 0)
        
        with pytest.raises(json.JSONDecodeError):
            validate_export_consistency(json_path, csv_path)

    def test_validate_export_consistency_malformed_csv(self, tmp_path):
        """Test handling of malformed CSV (missing headers)."""
        json_path = create_valid_audit_json(tmp_path)
        csv_path = tmp_path / "malformed.csv"
        with open(csv_path, "w") as f:
            f.write("total_summaries,inconsistent_count\n1,1") # Missing required headers
        
        with pytest.raises(KeyError):
            validate_export_consistency(json_path, csv_path)