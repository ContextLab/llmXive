"""
Test suite for T040: Run pytest --cov=code and verify coverage report.

This module ensures that the coverage report is generated and contains
valid numeric values for line and branch coverage.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


class TestCoverageExecution:
    """Tests for coverage execution and report validation."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Ensure we have a clean environment for testing."""
        self.project_root = Path(__file__).parent.parent
        self.code_dir = self.project_root / "code"
        self.coverage_xml = self.project_root / "coverage.xml"
        self.coverage_html_dir = self.project_root / "htmlcov"
        yield

    def test_pytest_cov_runs_successfully(self):
        """
        Verify that `pytest --cov=code` executes without error.
        """
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--cov=code",
                "--cov-report=xml",
                "--cov-report=html",
                "--cov-fail-under=0",  # Don't fail on low coverage
                "-v",
                str(self.project_root / "tests"),
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, (
            f"pytest failed with code {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    def test_coverage_xml_exists(self):
        """Verify that coverage.xml is generated."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--cov=code",
                "--cov-report=xml",
                "--cov-fail-under=0",
                "-q",
                str(self.project_root / "tests"),
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, "pytest failed"
        assert self.coverage_xml.exists(), "coverage.xml was not generated"

    def test_coverage_xml_contains_numeric_metrics(self):
        """
        Verify that coverage.xml contains numeric line and branch coverage.
        """
        # Ensure the report exists
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--cov=code",
                "--cov-report=xml",
                "--cov-fail-under=0",
                "-q",
                str(self.project_root / "tests"),
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )

        assert self.coverage_xml.exists(), "coverage.xml missing"

        import xml.etree.ElementTree as ET

        tree = ET.parse(self.coverage_xml)
        root = tree.getroot()

        # Check for line-rate (line coverage) and branch-rate (branch coverage)
        # in the 'coverage' tag
        line_rate = root.get("line-rate")
        branch_rate = root.get("branch-rate")

        assert line_rate is not None, "line-rate attribute missing in coverage.xml"
        assert branch_rate is not None, "branch-rate attribute missing in coverage.xml"

        # Verify they are numeric
        try:
            line_val = float(line_rate)
            branch_val = float(branch_rate)
        except ValueError:
            pytest.fail(f"Coverage values are not numeric: line={line_rate}, branch={branch_rate}")

        # Verify they are within valid range [0, 1]
        assert 0.0 <= line_val <= 1.0, f"Line rate {line_val} out of range [0, 1]"
        assert 0.0 <= branch_val <= 1.0, f"Branch rate {branch_val} out of range [0, 1]"

    def test_html_report_generated(self):
        """Verify that HTML coverage report is generated."""
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--cov=code",
                "--cov-report=html",
                "--cov-fail-under=0",
                "-q",
                str(self.project_root / "tests"),
            ],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )

        index_html = self.coverage_html_dir / "index.html"
        assert index_html.exists(), "HTML coverage report (index.html) not found"
