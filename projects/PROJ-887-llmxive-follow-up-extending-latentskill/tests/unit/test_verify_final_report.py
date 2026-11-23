"""
Unit tests for src/evaluation/verify_final_report.py (Task T080).
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.evaluation.verify_final_report import validate_report, REQUIRED_SECTIONS

class TestVerifyFinalReport:
    """Test cases for the final report validation logic."""

    def test_report_exists_and_valid(self, tmp_path):
        """Test validation when report exists and contains all sections."""
        report_path = tmp_path / "final_report.md"
        content = """
        # Final Report

        ## Statistical Power
        The power estimate is 0.85.

        ## Zero-Variance Incidents
        No incidents detected.

        ## Data Integrity
        All data is real.
        """
        report_path.write_text(content)

        result = validate_report(report_path)

        assert result["exists"] is True
        assert result["valid"] is True
        assert len(result["missing_sections"]) == 0
        assert all(s in result["found_sections"] for s in REQUIRED_SECTIONS)

    def test_report_exists_but_missing_sections(self, tmp_path):
        """Test validation when report exists but misses sections."""
        report_path = tmp_path / "final_report.md"
        content = """
        # Final Report

        ## Statistical Power
        The power estimate is 0.85.
        """
        report_path.write_text(content)

        result = validate_report(report_path)

        assert result["exists"] is True
        assert result["valid"] is False
        assert len(result["missing_sections"]) == 2
        assert "Zero-Variance Incidents" in result["missing_sections"]
        assert "Data Integrity" in result["missing_sections"]

    def test_report_not_exists(self, tmp_path):
        """Test validation when report file does not exist."""
        report_path = tmp_path / "nonexistent.md"

        result = validate_report(report_path)

        assert result["exists"] is False
        assert result["valid"] is False
        assert "File not found" in result["error"]

    def test_case_insensitive_search(self, tmp_path):
        """Test that section search is case-insensitive."""
        report_path = tmp_path / "final_report.md"
        content = """
        # Final Report

        ## statistical power
        ## zero-variance incidents
        ## DATA INTEGRITY
        """
        report_path.write_text(content)

        result = validate_report(report_path)

        assert result["valid"] is True
        assert len(result["missing_sections"]) == 0

    def test_empty_report(self, tmp_path):
        """Test validation on an empty file."""
        report_path = tmp_path / "final_report.md"
        report_path.write_text("")

        result = validate_report(report_path)

        assert result["valid"] is False
        assert len(result["missing_sections"]) == len(REQUIRED_SECTIONS)