"""Unit tests for linting report functionality.

Tests the linting report generator to ensure it correctly:
- Runs black checks
- Parses violations
- Generates reports
"""

import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from reproducibility.linting_report import (
    LintingViolation,
    LintingReport,
    get_black_version,
    run_black_check,
    count_python_files,
    generate_linting_report,
    write_linting_report_md,
)


class TestLintingViolation:
    """Tests for LintingViolation dataclass."""

    def test_violation_creation(self):
        """Test creating a linting violation."""
        violation = LintingViolation(
            file_path="test.py",
            line_number=10,
            column_number=5,
            message="Line too long",
            code="black"
        )

        assert violation.file_path == "test.py"
        assert violation.line_number == 10
        assert violation.column_number == 5
        assert violation.message == "Line too long"
        assert violation.code == "black"

    def test_violation_to_dict(self):
        """Test converting violation to dictionary."""
        violation = LintingViolation(
            file_path="test.py",
            line_number=10,
            column_number=5,
            message="Line too long",
            code="black"
        )

        result = violation.to_dict()
        assert result["file_path"] == "test.py"
        assert result["line_number"] == 10
        assert result["column_number"] == 5
        assert result["message"] == "Line too long"
        assert result["code"] == "black"


class TestLintingReport:
    """Tests for LintingReport dataclass."""

    def test_report_creation(self):
        """Test creating a linting report."""
        report = LintingReport(
            timestamp="2026-06-02T12:00:00",
            black_version="black, 24.3.0",
            files_checked=10,
            files_with_violations=0,
            total_violations=0,
            cleanup_status="passed"
        )

        assert report.timestamp == "2026-06-02T12:00:00"
        assert report.black_version == "black, 24.3.0"
        assert report.files_checked == 10
        assert report.files_with_violations == 0
        assert report.total_violations == 0
        assert report.cleanup_status == "passed"

    def test_report_with_violations(self):
        """Test report with violations."""
        violations = [
            LintingViolation(
                file_path="test.py",
                line_number=10,
                column_number=5,
                message="Line too long",
                code="black"
            )
        ]

        report = LintingReport(
            timestamp="2026-06-02T12:00:00",
            black_version="black, 24.3.0",
            files_checked=10,
            files_with_violations=1,
            total_violations=1,
            violations=violations,
            cleanup_status="failed"
        )

        assert report.cleanup_status == "failed"
        assert len(report.violations) == 1

    def test_report_to_dict(self):
        """Test converting report to dictionary."""
        violations = [
            LintingViolation(
                file_path="test.py",
                line_number=10,
                column_number=5,
                message="Line too long",
                code="black"
            )
        ]

        report = LintingReport(
            timestamp="2026-06-02T12:00:00",
            black_version="black, 24.3.0",
            files_checked=10,
            files_with_violations=1,
            total_violations=1,
            violations=violations,
            cleanup_status="failed"
        )

        result = report.to_dict()
        assert result["timestamp"] == "2026-06-02T12:00:00"
        assert result["files_checked"] == 10
        assert result["total_violations"] == 1
        assert len(result["violations"]) == 1
        assert result["violations"][0]["file_path"] == "test.py"


class TestGetBlackVersion:
    """Tests for get_black_version function."""

    @patch("subprocess.run")
    def test_get_version_success(self, mock_run):
        """Test successful version retrieval."""
        mock_run.return_value = MagicMock(
            stdout="black, 24.3.0 (compiled: yes)\n"
        )

        version = get_black_version()
        assert version == "black, 24.3.0 (compiled: yes)"

    @patch("subprocess.run")
    def test_get_version_failure(self, mock_run):
        """Test failed version retrieval."""
        mock_run.side_effect = FileNotFoundError()

        version = get_black_version()
        assert version is None


class TestRunBlackCheck:
    """Tests for run_black_check function."""

    @patch("subprocess.run")
    def test_no_violations(self, mock_run):
        """Test when no violations found."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr=""
        )

        code_dir = Path("/fake/code")
        return_code, violations = run_black_check(code_dir)

        assert return_code == 0
        assert len(violations) == 0

    @patch("subprocess.run")
    def test_with_violations(self, mock_run):
        """Test when violations are found."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="test.py:10:5: Line too long (90 > 88 characters)"
        )

        code_dir = Path("/fake/code")
        return_code, violations = run_black_check(code_dir)

        assert return_code == 1
        assert len(violations) == 1
        assert violations[0].file_path == "test.py"
        assert violations[0].line_number == 10
        assert violations[0].column_number == 5
        assert "Line too long" in violations[0].message

    @patch("subprocess.run")
    def test_exception_handling(self, mock_run):
        """Test exception handling."""
        mock_run.side_effect = Exception("Test error")

        code_dir = Path("/fake/code")
        return_code, violations = run_black_check(code_dir)

        assert return_code == 1
        assert len(violations) == 0


class TestCountPythonFiles:
    """Tests for count_python_files function."""

    def test_count_files(self, tmp_path):
        """Test counting Python files."""
        # Create test files
        (tmp_path / "file1.py").touch()
        (tmp_path / "file2.py").touch()
        (tmp_path / "file3.txt").touch()
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file4.py").touch()

        count = count_python_files(tmp_path)
        assert count == 3


class TestWriteLintingReportMd:
    """Tests for write_linting_report_md function."""

    def test_write_report_passed(self, tmp_path):
        """Test writing report with passed status."""
        report = LintingReport(
            timestamp="2026-06-02T12:00:00",
            black_version="black, 24.3.0",
            files_checked=10,
            files_with_violations=0,
            total_violations=0,
            cleanup_status="passed"
        )

        output_path = tmp_path / "docs" / "reproducibility" / "linting_report.md"
        write_linting_report_md(report, output_path)

        content = output_path.read_text()
        assert "Linting Report" in content
        assert "passed" in content
        assert "All files pass black linting standards" in content

    def test_write_report_failed(self, tmp_path):
        """Test writing report with failed status."""
        violations = [
            LintingViolation(
                file_path="test.py",
                line_number=10,
                column_number=5,
                message="Line too long",
                code="black"
            )
        ]

        report = LintingReport(
            timestamp="2026-06-02T12:00:00",
            black_version="black, 24.3.0",
            files_checked=10,
            files_with_violations=1,
            total_violations=1,
            violations=violations,
            cleanup_status="failed"
        )

        output_path = tmp_path / "docs" / "reproducibility" / "linting_report.md"
        write_linting_report_md(report, output_path)

        content = output_path.read_text()
        assert "Linting Report" in content
        assert "failed" in content
        assert "test.py" in content
        assert "10" in content
        assert "Line too long" in content