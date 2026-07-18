"""
Unit tests for the terminology scanner.

These tests verify that the scanner correctly identifies forbidden terms
and allows legitimate scientific context (citations, negations, etc.).
"""

import os
import json
import tempfile
from pathlib import Path
import pytest

from utils.terminology_scanner import (
    scan_file,
    is_acceptable_context,
    run_audit,
    FORBIDDEN_PATTERNS,
    ACCEPTABLE_CONTEXTS
)

class TestAcceptableContext:
    """Tests for the context detection logic."""

    def test_negation_context(self):
        """Should accept terms when negated."""
        line = "This model does NOT solve the Schrödinger equation."
        match_start = line.find("Schrödinger")
        match_end = match_start + len("Schrödinger")
        assert is_acceptable_context(line, match_start, match_end) is True

    def test_comparison_context(self):
        """Should accept terms in comparison contexts."""
        line = "Unlike first-principles methods, this is a surrogate."
        match_start = line.find("first-principles")
        match_end = match_start + len("first-principles")
        assert is_acceptable_context(line, match_start, match_end) is True

    def test_citation_context(self):
        """Should accept terms in citation contexts."""
        line = "As described by Smith et al., the Hamiltonian approach is different."
        match_start = line.find("Hamiltonian")
        match_end = match_start + len("Hamiltonian")
        assert is_acceptable_context(line, match_start, match_end) is True

    def test_violation_context(self):
        """Should flag terms in violation contexts."""
        line = "We solve the Schrödinger equation for all materials."
        match_start = line.find("Schrödinger")
        match_end = match_start + len("Schrödinger")
        assert is_acceptable_context(line, match_start, match_end) is False

    def test_warning_context(self):
        """Should accept terms in warning contexts."""
        line = "WARNING: This does not calculate the Hamiltonian."
        match_start = line.find("Hamiltonian")
        match_end = match_start + len("Hamiltonian")
        assert is_acceptable_context(line, match_start, match_end) is True

class TestScanFile:
    """Tests for the file scanning logic."""

    def test_scan_forbidden_term(self):
        """Should detect forbidden terms in files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This model solves the Schrödinger equation.\n")
            f.write("It calculates from the Hamiltonian.\n")
            temp_path = Path(f.name)

        try:
            violations = scan_file(temp_path, temp_path.parent)
            assert len(violations) == 2
            assert any("Schrödinger" in v.pattern_matched for v in violations)
            assert any("Hamiltonian" in v.pattern_matched for v in violations)
        finally:
            os.unlink(temp_path)

    def test_scan_acceptable_context(self):
        """Should not flag terms in acceptable contexts."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This model does NOT solve the Schrödinger equation.\n")
            f.write("Unlike first-principles, this is a surrogate.\n")
            temp_path = Path(f.name)

        try:
            violations = scan_file(temp_path, temp_path.parent)
            assert len(violations) == 0
        finally:
            os.unlink(temp_path)

    def test_scan_mixed_content(self):
        """Should detect only violations in mixed content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This model does NOT solve the Schrödinger equation.\n")
            f.write("But it DOES calculate the Hamiltonian.\n")
            temp_path = Path(f.name)

        try:
            violations = scan_file(temp_path, temp_path.parent)
            assert len(violations) == 1
            assert "Hamiltonian" in violations[0].pattern_matched
        finally:
            os.unlink(temp_path)

    def test_scan_binary_file(self):
        """Should skip binary files."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
            f.write(b'\x89PNG\r\n\x1a\n')
            temp_path = Path(f.name)

        try:
            violations = scan_file(temp_path, temp_path.parent)
            assert len(violations) == 0
        finally:
            os.unlink(temp_path)

class TestRunAudit:
    """Tests for the full audit workflow."""

    def test_audit_creates_report(self):
        """Should create a valid JSON report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            output_path = project_root / 'data' / 'results' / 'terminology_audit.json'

            # Create a test file with a violation
            code_dir = project_root / 'code'
            code_dir.mkdir(parents=True)
            test_file = code_dir / 'test.txt'
            test_file.write_text("This solves the equation.\n")

            # Run audit
            report = run_audit(project_root, output_path)

            # Verify report structure
            assert output_path.exists()
            assert report.total_violations == 1
            assert report.total_files_scanned == 1

            # Verify JSON is valid
            with open(output_path, 'r') as f:
                data = json.load(f)
            assert 'violations' in data
            assert 'summary' in data

    def test_audit_excludes_data_results(self):
        """Should not scan data/results directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            output_path = project_root / 'data' / 'results' / 'terminology_audit.json'

            # Create a violation in data/results (should be excluded)
            data_results_dir = project_root / 'data' / 'results'
            data_results_dir.mkdir(parents=True)
            test_file = data_results_dir / 'violation.txt'
            test_file.write_text("This solves the equation.\n")

            # Create a violation in code (should be included)
            code_dir = project_root / 'code'
            code_dir.mkdir(parents=True)
            test_file2 = code_dir / 'code.txt'
            test_file2.write_text("This solves the equation.\n")

            # Run audit
            report = run_audit(project_root, output_path)

            # Should only find 1 violation (in code/)
            assert report.total_violations == 1
            assert report.violations[0].file_path == 'code/code.txt'

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_file(self):
        """Should handle empty files gracefully."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_path = Path(f.name)

        try:
            violations = scan_file(temp_path, temp_path.parent)
            assert len(violations) == 0
        finally:
            os.unlink(temp_path)

    def test_unicode_content(self):
        """Should handle Unicode content correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("This solves the Schrödinger equation.\n")
            f.write("日本語テスト\n")
            temp_path = Path(f.name)

        try:
            violations = scan_file(temp_path, temp_path.parent)
            assert len(violations) == 1
            assert "Schrödinger" in violations[0].pattern_matched
        finally:
            os.unlink(temp_path)

    def test_case_insensitive(self):
        """Should be case-insensitive."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This solves the SCHRÖDINGER equation.\n")
            f.write("This solves the schrodinger equation.\n")
            temp_path = Path(f.name)

        try:
            violations = scan_file(temp_path, temp_path.parent)
            assert len(violations) == 2
        finally:
            os.unlink(temp_path)

    def test_partial_matches(self):
        """Should not match partial words."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a Schrödingerian model.\n")  # Should not match
            f.write("This solves the equation.\n")  # Should match
            temp_path = Path(f.name)

        try:
            violations = scan_file(temp_path, temp_path.parent)
            assert len(violations) == 1
            assert "equation" in violations[0].pattern_matched.lower()
        finally:
            os.unlink(temp_path)
