"""
Tests for verifying the project directory structure.
Specifically validates that T001c (data/processed) and other setup tasks exist.
"""
import os
import pytest
from pathlib import Path

def test_data_processed_directory_exists():
    """Verify that data/processed/ directory exists at the project root."""
    project_root = Path(__file__).parent.parent
    processed_dir = project_root / "data" / "processed"
    assert processed_dir.exists(), f"Directory {processed_dir} does not exist."
    assert processed_dir.is_dir(), f"{processed_dir} is not a directory."

def test_code_directory_exists():
    """Verify that code/ directory exists (T001a)."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    assert code_dir.exists(), f"Directory {code_dir} does not exist."

def test_data_raw_directory_exists():
    """Verify that data/raw/ directory exists (T001b)."""
    project_root = Path(__file__).parent.parent
    raw_dir = project_root / "data" / "raw"
    assert raw_dir.exists(), f"Directory {raw_dir} does not exist."

def test_tests_directory_exists():
    """Verify that tests/ directory exists (T001d)."""
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    assert tests_dir.exists(), f"Directory {tests_dir} does not exist."