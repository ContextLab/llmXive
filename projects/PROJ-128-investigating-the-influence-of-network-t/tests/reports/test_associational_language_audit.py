"""
Unit tests for the Associational Language Compliance Audit (T043).
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from reports.audit_associational_language import (
    check_text_for_causality,
    scan_report_json,
    scan_csv_file,
    generate_audit_report
)

class TestCausalityDetection:
    """Test the core regex detection logic."""

    def test_detects_predicts(self):
        text = "The structural network predicts the functional state."
        findings = check_text_for_causality(text, "test")
        assert len(findings) == 1
        assert "predicts" in findings[0]["term"]

    def test_detects_causes(self):
        text = "This causes that to happen."
        findings = check_text_for_causality(text, "test")
        assert len(findings) == 1
        assert "causes" in findings[0]["term"]

    def test_accepts_correlates(self):
        text = "The network correlates with the activity."
        findings = check_text_for_causality(text, "test")
        assert len(findings) == 0

    def test_accepts_associates(self):
        text = "We observe an association between X and Y."
        findings = check_text_for_causality(text, "test")
        assert len(findings) == 0

    def test_case_insensitive(self):
        text = "STRUCTURE PREDICTS FUNCTION."
        findings = check_text_for_causality(text, "test")
        assert len(findings) == 1

    def test_empty_string(self):
        text = ""
        findings = check_text_for_causality(text, "test")
        assert len(findings) == 0

class TestReportScanning:
    """Test scanning nested JSON structures."""

    def test_scan_nested_dict(self):
        data = {
            "summary": "Structure predicts function.",
            "details": {
                "finding": "Strong correlation observed."
            }
        }
        findings = scan_report_json(data)
        assert len(findings) == 1
        assert findings[0]["context"] == "root.summary"

    def test_scan_list(self):
        data = {
            "results": [
                "First predicts second.",
                "Third correlates with fourth."
            ]
        }
        findings = scan_report_json(data)
        assert len(findings) == 1
        assert "results[0]" in findings[0]["context"]

class TestCSVScanning:
    """Test scanning CSV lines."""

    def test_scan_csv_with_violation(self):
        lines = [
            "metric,value,p_value",
            "efficiency,0.5,0.01",
            "This predicts that,0.8,0.001"
        ]
        findings = scan_csv_file(lines)
        assert len(findings) == 1
        assert "Line 3" in findings[0]["context"]

    def test_scan_csv_clean(self):
        lines = [
            "metric,value,p_value",
            "efficiency,0.5,0.01",
            "correlation,0.8,0.001"
        ]
        findings = scan_csv_file(lines)
        assert len(findings) == 0

class TestAuditReportGeneration:
    """Test the generation of the audit log file."""

    def test_generate_compliant_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit.json"
            is_compliant = generate_audit_report([], audit_path)
            
            assert is_compliant is True
            assert audit_path.exists()
            
            with open(audit_path, 'r') as f:
                data = json.load(f)
            
            assert data["compliant"] is True
            assert data["total_findings"] == 0

    def test_generate_non_compliant_report(self):
        findings = [{"term": "predicts", "context": "root"}]
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = Path(tmpdir) / "audit.json"
            is_compliant = generate_audit_report(findings, audit_path)
            
            assert is_compliant is False
            assert audit_path.exists()
            
            with open(audit_path, 'r') as f:
                data = json.load(f)
            
            assert data["compliant"] is False
            assert data["total_findings"] == 1