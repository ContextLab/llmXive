"""
Tests to verify the project structure directories exist.
"""
import os
import pytest
from pathlib import Path

def test_code_directory_exists(project_root):
    """Verify code/ directory exists."""
    assert (project_root / "code").exists(), "code/ directory does not exist"
    assert (project_root / "code").is_dir(), "code/ is not a directory"

def test_data_raw_directory_exists(project_root):
    """Verify data/raw/ directory exists."""
    assert (project_root / "data" / "raw").exists(), "data/raw/ directory does not exist"
    assert (project_root / "data" / "raw").is_dir(), "data/raw/ is not a directory"

def test_data_processed_directory_exists(project_root):
    """Verify data/processed/ directory exists."""
    assert (project_root / "data" / "processed").exists(), "data/processed/ directory does not exist"
    assert (project_root / "data" / "processed").is_dir(), "data/processed/ is not a directory"

def test_tests_directory_exists(project_root):
    """Verify tests/ directory exists."""
    assert (project_root / "tests").exists(), "tests/ directory does not exist"
    assert (project_root / "tests").is_dir(), "tests/ is not a directory"

def test_artifacts_reports_directory_exists(project_root):
    """Verify artifacts/reports/ directory exists."""
    assert (project_root / "artifacts" / "reports").exists(), "artifacts/reports/ directory does not exist"
    assert (project_root / "artifacts" / "reports").is_dir(), "artifacts/reports/ is not a directory"

def test_artifacts_figures_directory_exists(project_root):
    """Verify artifacts/figures/ directory exists."""
    assert (project_root / "artifacts" / "figures").exists(), "artifacts/figures/ directory does not exist"
    assert (project_root / "artifacts" / "figures").is_dir(), "artifacts/figures/ is not a directory"

def test_state_directory_exists(project_root):
    """Verify state/ directory exists."""
    assert (project_root / "state").exists(), "state/ directory does not exist"
    assert (project_root / "state").is_dir(), "state/ is not a directory"
