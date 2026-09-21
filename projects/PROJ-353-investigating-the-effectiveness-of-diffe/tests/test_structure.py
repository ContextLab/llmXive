"""
Unit tests for project structure verification.
"""
import os
from pathlib import Path
import pytest

@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent

def test_code_directory_exists(project_root):
    """Test that the code/ directory exists."""
    code_dir = project_root / "code"
    assert code_dir.exists(), "code/ directory must exist"
    assert code_dir.is_dir(), "code/ must be a directory"

def test_tests_directory_exists(project_root):
    """Test that the tests/ directory exists."""
    tests_dir = project_root / "tests"
    assert tests_dir.exists(), "tests/ directory must exist"
    assert tests_dir.is_dir(), "tests/ must be a directory"

def test_data_raw_directory_exists(project_root):
    """Test that data/raw/ directory exists."""
    raw_dir = project_root / "data" / "raw"
    assert raw_dir.exists(), "data/raw/ directory must exist"
    assert raw_dir.is_dir(), "data/raw/ must be a directory"

def test_data_logs_directory_exists(project_root):
    """Test that data/logs/ directory exists."""
    logs_dir = project_root / "data" / "logs"
    assert logs_dir.exists(), "data/logs/ directory must exist"
    assert logs_dir.is_dir(), "data/logs/ must be a directory"

def test_data_analysis_directory_exists(project_root):
    """Test that data/analysis/ directory exists."""
    analysis_dir = project_root / "data" / "analysis"
    assert analysis_dir.exists(), "data/analysis/ directory must exist"
    assert analysis_dir.is_dir(), "data/analysis/ must be a directory"

def test_code_init_file_exists(project_root):
    """Test that code/__init__.py exists."""
    init_file = project_root / "code" / "__init__.py"
    assert init_file.exists(), "code/__init__.py must exist"

def test_tests_init_file_exists(project_root):
    """Test that tests/__init__.py exists."""
    init_file = project_root / "tests" / "__init__.py"
    assert init_file.exists(), "tests/__init__.py must exist"