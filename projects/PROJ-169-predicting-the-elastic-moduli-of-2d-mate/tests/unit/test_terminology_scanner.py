"""
Unit tests for the terminology scanner.
"""
import pytest
from pathlib import Path
import tempfile
import os
import json

# Import the module under test
# We assume the scanner logic is in code/utils/terminology_scanner.py
# We need to add the code directory to the path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from utils.terminology_scanner import (
    is_acceptable_context,
    Violation,
    AuditReport,
    scan_file,
    run_audit
)

class TestIsAcceptableContext:
    def test_negative_context(self):
        line = "This model is NOT a first-principles calculation."
        assert is_acceptable_context(line, "first-principles") is True

    def test_positive_context(self):
        line = "We perform first-principles calculations to train the model."
        assert is_acceptable_context(line, "first-principles") is False

    def test_disclaimer_context(self):
        line = "Note: This does NOT solve the Schrödinger equation."
        assert is_acceptable_context(line, "Schrödinger") is True

    def test_no_context(self):
        line = "The first-principles approach is used here."
        assert is_acceptable_context(line, "first-principles") is False

class TestViolation:
    def test_to_dict(self):
        v = Violation("test.py", 10, "First-Principles", "Surrogate", "Some code line")
        d = v.to_dict()
        assert d["file"] == "test.py"
        assert d["line"] == 10
        assert d["original"] == "First-Principles"
        assert d["replacement"] == "Surrogate"
        assert "Some code line" in d["context"]

class TestAuditReport:
    def test_add_violation(self):
        r = AuditReport()
        v = Violation("test.py", 1, "A", "B", "C")
        r.add_violation(v)
        assert len(r.violations) == 1

    def test_to_dict(self):
        r = AuditReport()
        r.files_scanned = 5
        r.files_modified = 2
        r.add_violation(Violation("test.py", 1, "A", "B", "C"))
        d = r.to_dict()
        assert d["summary"]["files_scanned"] == 5
        assert d["summary"]["files_modified"] == 2
        assert len(d["violations"]) == 1

class TestScanFile:
    def test_scan_file_modification(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            content = "This is a First-Principles calculation.\n"
            with open(file_path, 'w') as f:
                f.write(content)

            report = AuditReport()
            modified = scan_file(file_path, report)

            assert modified is True
            assert len(report.violations) == 1

            with open(file_path, 'r') as f:
                new_content = f.read()

            assert "Surrogate" in new_content
            assert "First-Principles" not in new_content

    def test_scan_file_no_modification(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            content = "This is a Surrogate model.\n"
            with open(file_path, 'w') as f:
                f.write(content)

            report = AuditReport()
            modified = scan_file(file_path, report)

            assert modified is False
            assert len(report.violations) == 0

    def test_scan_file_acceptable_context(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            content = "This is NOT a First-Principles calculation.\n"
            with open(file_path, 'w') as f:
                f.write(content)

            report = AuditReport()
            modified = scan_file(file_path, report)

            # Should not modify because it's in a negative context
            assert modified is False
            assert len(report.violations) == 0