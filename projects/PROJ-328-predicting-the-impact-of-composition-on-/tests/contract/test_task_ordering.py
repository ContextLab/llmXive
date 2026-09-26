"""
Contract Test for Task Ordering (T058).
Verifies that the dependency chain is correctly implemented and artifacts are generated.
"""
import os
import json
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
AUDIT_REPORT_PATH = PROJECT_ROOT / "data" / "outputs" / "task_ordering_audit.json"
CLEANED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "solder_hardness_cleaned.csv"
CLR_FEATURES_PATH = PROJECT_ROOT / "data" / "processed" / "clr_features.csv"
DESCRIPTORS_PATH = PROJECT_ROOT / "data" / "processed" / "descriptors.csv"
INGESTION_STATUS_PATH = PROJECT_ROOT / "data" / "processed" / ".ingestion_status.json"

def test_audit_report_exists():
    """Test that the audit report is generated."""
    assert AUDIT_REPORT_PATH.exists(), "Audit report not found."

def test_audit_report_structure():
    """Test that the audit report has the correct structure."""
    if not AUDIT_REPORT_PATH.exists():
        pytest.skip("Audit report not found.")
    
    with open(AUDIT_REPORT_PATH, 'r') as f:
        report = json.load(f)
    
    assert "dependency_chain" in report, "Missing dependency_chain in report."
    assert "synthetic_data_usage" in report, "Missing synthetic_data_usage in report."
    assert "passed" in report, "Missing passed status in report."

def test_artifacts_exist():
    """Test that all required artifacts are generated."""
    assert CLEANED_DATA_PATH.exists(), "Cleaned data file missing."
    assert CLR_FEATURES_PATH.exists(), "CLR features file missing."
    assert DESCRIPTORS_PATH.exists(), "Descriptors file missing."
    assert INGESTION_STATUS_PATH.exists(), "Ingestion status file missing."

def test_no_synthetic_data_in_audit():
    """Test that no synthetic data was used in the audit process."""
    if not AUDIT_REPORT_PATH.exists():
        pytest.skip("Audit report not found.")
    
    with open(AUDIT_REPORT_PATH, 'r') as f:
        report = json.load(f)
    
    assert report.get("passed", False), "Audit failed: Synthetic data detected or dependencies missing."
    assert len(report.get("synthetic_data_usage", {})) == 0, "Synthetic data detected in audit."