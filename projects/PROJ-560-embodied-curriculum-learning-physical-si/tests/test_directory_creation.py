"""
Tests for directory creation functionality.
Verifies that required directories are created by setup scripts.
"""
import os
import pytest
from pathlib import Path
import tempfile
import shutil


def test_code_src_directory_exists():
    """Test that code/src/ directory exists."""
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "code" / "src"
    assert src_dir.exists(), f"Directory {src_dir} does not exist"
    assert src_dir.is_dir(), f"{src_dir} is not a directory"


def test_code_tests_directory_exists():
    """Test that code/tests/ directory exists."""
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "code" / "tests"
    assert tests_dir.exists(), f"Directory {tests_dir} does not exist"
    assert tests_dir.is_dir(), f"{tests_dir} is not a directory"


def test_src_init_exists():
    """Test that code/src/__init__.py exists."""
    project_root = Path(__file__).parent.parent
    init_file = project_root / "code" / "src" / "__init__.py"
    assert init_file.exists(), f"File {init_file} does not exist"
    assert init_file.is_file(), f"{init_file} is not a file"


def test_tests_init_exists():
    """Test that code/tests/__init__.py exists."""
    project_root = Path(__file__).parent.parent
    init_file = project_root / "code" / "tests" / "__init__.py"
    assert init_file.exists(), f"File {init_file} does not exist"
    assert init_file.is_file(), f"{init_file} is not a file"


def test_data_raw_directory_exists():
    """Test that data/raw/ directory exists."""
    project_root = Path(__file__).parent.parent
    raw_dir = project_root / "data" / "raw"
    assert raw_dir.exists(), f"Directory {raw_dir} does not exist"
    assert raw_dir.is_dir(), f"{raw_dir} is not a directory"


def test_data_processed_directory_exists():
    """Test that data/processed/ directory exists."""
    project_root = Path(__file__).parent.parent
    processed_dir = project_root / "data" / "processed"
    assert processed_dir.exists(), f"Directory {processed_dir} does not exist"
    assert processed_dir.is_dir(), f"{processed_dir} is not a directory"


def test_data_synthetic_directory_exists():
    """Test that data/synthetic/ directory exists."""
    project_root = Path(__file__).parent.parent
    synthetic_dir = project_root / "data" / "synthetic"
    assert synthetic_dir.exists(), f"Directory {synthetic_dir} does not exist"
    assert synthetic_dir.is_dir(), f"{synthetic_dir} is not a directory"


def test_data_derivation_logs_directory_exists():
    """Test that data/derivation_logs/ directory exists."""
    project_root = Path(__file__).parent.parent
    logs_dir = project_root / "data" / "derivation_logs"
    assert logs_dir.exists(), f"Directory {logs_dir} does not exist"
    assert logs_dir.is_dir(), f"{logs_dir} is not a directory"


def test_setup_data_dirs_creates_directories():
    """Test that setup_data_dirs.py creates all required directories."""
    # Create a temporary directory to simulate project root
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create code directory structure
        code_dir = temp_path / "code"
        code_dir.mkdir()
        
        # Import the setup function
        import sys
        sys.path.insert(0, str(temp_path))
        
        # We need to test the logic of create_directory
        from setup_data_dirs import create_directory
        
        # Test directory creation
        test_dir = temp_path / "test_data" / "new_dir"
        result = create_directory(test_dir)
        
        assert result is True, "create_directory should return True on success"
        assert test_dir.exists(), "Directory should be created"
        assert test_dir.is_dir(), "Created path should be a directory"
        
        # Test that it doesn't fail on existing directory
        result = create_directory(test_dir)
        assert result is True, "create_directory should return True for existing dir"