"""
Unit tests for the linting utilities.
"""
import os
import tempfile
from pathlib import Path

import pytest

from code.linting import run_flake8, verify_pep8_compliance


def test_run_flake8_on_clean_directory(tmp_path):
    """
    Test that run_flake8 returns True for a directory with clean Python files.
    """
    # Create a temporary directory with a simple, compliant Python file
    clean_file = tmp_path / "clean.py"
    clean_file.write_text("x = 1\n")

    success, output = run_flake8(str(tmp_path))

    assert success is True
    assert "No violations" in output or output == "No violations found."


def test_run_flake8_on_violation_directory(tmp_path):
    """
    Test that run_flake8 returns False for a directory with PEP8 violations.
    """
    # Create a temporary directory with a file containing a violation
    # (e.g., line too long or missing newline at end of file)
    violation_file = tmp_path / "violation.py"
    # A line exceeding 120 characters (our max-line-length setting)
    long_line = "x = " + "a" * 120 + "\n"
    violation_file.write_text(long_line)

    success, output = run_flake8(str(tmp_path))

    assert success is False
    assert "E501" in output or "too long" in output.lower()


def test_verify_pep8_compliance_returns_bool(tmp_path):
    """
    Test that verify_pep8_compliance returns a boolean.
    """
    result = verify_pep8_compliance(str(tmp_path))
    assert isinstance(result, bool)
