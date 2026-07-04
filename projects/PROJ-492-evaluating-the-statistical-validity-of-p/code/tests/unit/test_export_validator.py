"""
Unit tests for the export validator (T060).

This module verifies that the export_validator correctly detects inconsistencies
between the JSON audit report and the CSV summary report.
"""
import json
import csv
import tempfile
import os
import pytest
from pathlib import Path
from typing import Dict, Any, List

from code.src.audit.export_validator import (
    load_audit_records_from_json,
    load_summary_counts_from_csv,
    validate_export_consistency,
    run_export_validation
)


def create_temp_json_file(records: List[Dict[str, Any]], filename: str = "audit_report.json") -> Path:
    """Helper to create a temporary JSON file with audit records."""
    fd, path = tempfile.mkstemp(suffix=".json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(records, f)
    finally:
        os.close(fd)
    return Path(path)


def create_temp_csv_file(total: int, inconsistent: int, filename: str = "summary_report.csv") -> Path:
    """Helper to create a temporary CSV file with summary counts."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["total_summaries", "inconsistent_count", "inconsistent_rate", "bias_adjusted_rate", "wilson_ci_lower", "wilson_ci_upper"])
            writer.writerow([total, inconsistent, inconsistent/total if total > 0 else 0.0, 0.0, 0.0, 0.0])
    finally:
        os.close(fd)
    return Path(path)


def test_export_validator_catches_mismatched_counts():
    """
    Verify that the export validator catches a deliberate mismatch between
    the JSON audit report and the CSV summary report.
    
    This is the core test for T060: Unit test for export validator with 
    deliberately mismatched files.
    """
    # Create a JSON file with 100 records, 10 inconsistent
    json_records = [
        {"id": i, "is_inconsistent": i % 10 == 0}  # 10% inconsistent
        for i in range(100)
    ]
    json_path = create_temp_json_file(json_records)
    
    # Create a CSV file claiming 100 total but 20 inconsistent (mismatch!)
    csv_path = create_temp_csv_file(total=100, inconsistent=20)
    
    # Run the validation
    json_data = load_audit_records_from_json(json_path)
    csv_counts = load_summary_counts_from_csv(csv_path)
    
    is_consistent, error_message = validate_export_consistency(json_data, csv_counts)
    
    # Assert that the mismatch was detected
    assert not is_consistent, "Export validator should detect count mismatch"
    assert "inconsistent_count" in error_message.lower() or "mismatch" in error_message.lower()
    
    # Clean up
    json_path.unlink()
    csv_path.unlink()


def test_export_validator_passes_when_consistent():
    """
    Verify that the export validator passes when JSON and CSV counts match.
    """
    # Create a JSON file with 50 records, 5 inconsistent
    json_records = [
        {"id": i, "is_inconsistent": i % 10 == 0}  # 10% inconsistent
        for i in range(50)
    ]
    json_path = create_temp_json_file(json_records)
    
    # Create a CSV file with matching counts
    csv_path = create_temp_csv_file(total=50, inconsistent=5)
    
    # Run the validation
    json_data = load_audit_records_from_json(json_path)
    csv_counts = load_summary_counts_from_csv(csv_path)
    
    is_consistent, error_message = validate_export_consistency(json_data, csv_counts)
    
    # Assert that consistency was confirmed
    assert is_consistent, "Export validator should pass when counts match"
    assert error_message is None or "mismatch" not in error_message.lower()
    
    # Clean up
    json_path.unlink()
    csv_path.unlink()


def test_export_validator_handles_empty_json():
    """
    Verify that the export validator handles an empty JSON file correctly.
    """
    json_records = []
    json_path = create_temp_json_file(json_records)
    
    # Create a CSV file claiming 0 total, 0 inconsistent
    csv_path = create_temp_csv_file(total=0, inconsistent=0)
    
    # Run the validation
    json_data = load_audit_records_from_json(json_path)
    csv_counts = load_summary_counts_from_csv(csv_path)
    
    is_consistent, error_message = validate_export_consistency(json_data, csv_counts)
    
    # Should be consistent (0 == 0)
    assert is_consistent, "Export validator should handle empty files consistently"
    
    # Clean up
    json_path.unlink()
    csv_path.unlink()


def test_export_validator_catches_total_count_mismatch():
    """
    Verify that the export validator catches a mismatch in total count.
    """
    # Create a JSON file with 80 records
    json_records = [{"id": i, "is_inconsistent": False} for i in range(80)]
    json_path = create_temp_json_file(json_records)
    
    # Create a CSV file claiming 100 total (mismatch!)
    csv_path = create_temp_csv_file(total=100, inconsistent=0)
    
    # Run the validation
    json_data = load_audit_records_from_json(json_path)
    csv_counts = load_summary_counts_from_csv(csv_path)
    
    is_consistent, error_message = validate_export_consistency(json_data, csv_counts)
    
    # Assert that the mismatch was detected
    assert not is_consistent, "Export validator should detect total count mismatch"
    
    # Clean up
    json_path.unlink()
    csv_path.unlink()


def test_export_validator_run_export_validation():
    """
    Test the high-level run_export_validation function.
    """
    # Create consistent files
    json_records = [{"id": i, "is_inconsistent": i < 5} for i in range(20)]
    json_path = create_temp_json_file(json_records)
    csv_path = create_temp_csv_file(total=20, inconsistent=5)
    
    # Should pass
    assert run_export_validation(json_path, csv_path) is True
    
    # Create inconsistent files
    csv_path_mismatch = create_temp_csv_file(total=20, inconsistent=10)
    
    # Should fail
    assert run_export_validation(json_path, csv_path_mismatch) is False
    
    # Clean up
    json_path.unlink()
    csv_path.unlink()
    csv_path_mismatch.unlink()