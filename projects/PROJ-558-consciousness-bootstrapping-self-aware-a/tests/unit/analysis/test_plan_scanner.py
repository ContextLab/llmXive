"""
Unit tests for the plan scanner (T003a).
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
from code.analysis.plan_scanner import scan_file

class TestPlanScanner:
    """Test cases for the plan scanner functionality."""

    def test_scan_file_with_matches(self, tmp_path):
        """Test scanning a file that contains the forbidden patterns."""
        # Create a temporary file with matches
        test_file = tmp_path / "test_plan.md"
        content = """
        # Test Plan

        This plan involves Teacher-Student Distillation.
        We also use Pre-computed Teacher Labels for training.
        Another line mentions external truth as a baseline.
        """
        test_file.write_text(content)

        matches = scan_file(str(test_file))

        assert len(matches) == 3
        assert any(m["pattern_matched"] == "Teacher-Student Distillation" for m in matches)
        assert any(m["pattern_matched"] == "Pre-computed Teacher Labels" for m in matches)
        assert any(m["pattern_matched"] == "external truth" for m in matches)

    def test_scan_file_without_matches(self, tmp_path):
        """Test scanning a file that does not contain the forbidden patterns."""
        # Create a temporary file without matches
        test_file = tmp_path / "test_plan.md"
        content = """
        # Test Plan

        This plan uses internal self-consistency.
        We rely on model-generated proxies.
        No external truth is used.
        """
        test_file.write_text(content)

        matches = scan_file(str(test_file))

        assert len(matches) == 0

    def test_scan_file_not_found(self, tmp_path):
        """Test scanning a non-existent file."""
        non_existent_file = tmp_path / "non_existent.md"

        matches = scan_file(str(non_existent_file))

        assert len(matches) == 0

    def test_scan_file_case_insensitive(self, tmp_path):
        """Test that the scan is case-insensitive."""
        test_file = tmp_path / "test_plan.md"
        content = """
        # Test Plan

        teacher-student distillation is mentioned.
        PRE-COMPUTED TEACHER LABELS are used.
        External Truth is the baseline.
        """
        test_file.write_text(content)

        matches = scan_file(str(test_file))

        assert len(matches) == 3