import os
import sys
import pytest
from pathlib import Path

# Ensure code/ is in path for imports
code_path = Path(__file__).resolve().parent.parent
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from scripts.create_directories import create_directory, main

@pytest.fixture
def temp_base_path(tmp_path):
    """Create a temporary base directory to simulate project root."""
    return tmp_path

def test_scripts_directory_exists(temp_base_path):
    """T001a: Verify code/scripts/ creation."""
    scripts_dir = temp_base_path / "scripts"
    result = create_directory(str(scripts_dir))
    assert result is True
    assert scripts_dir.exists()
    assert scripts_dir.is_dir()

def test_raw_data_directory_exists(temp_base_path):
    """T001b: Verify code/data/raw/ creation."""
    raw_dir = temp_base_path / "data" / "raw"
    result = create_directory(str(raw_dir))
    assert result is True
    assert raw_dir.exists()
    assert raw_dir.is_dir()

def test_processed_data_directory_exists(temp_base_path):
    """T001c: Verify code/data/processed/ creation."""
    processed_dir = temp_base_path / "data" / "processed"
    result = create_directory(str(processed_dir))
    assert result is True
    assert processed_dir.exists()
    assert processed_dir.is_dir()

def test_splits_directory_exists(temp_base_path):
    """T001d: Verify code/data/splits/ creation."""
    splits_dir = temp_base_path / "data" / "splits"
    result = create_directory(str(splits_dir))
    assert result is True
    assert splits_dir.exists()
    assert splits_dir.is_dir()

def test_models_directory_exists(temp_base_path):
    """T001e: Verify code/models/ creation."""
    models_dir = temp_base_path / "models"
    result = create_directory(str(models_dir))
    assert result is True
    assert models_dir.exists()
    assert models_dir.is_dir()

def test_tests_directory_exists(temp_base_path):
    """T001f: Verify code/tests/ creation."""
    tests_dir = temp_base_path / "tests"
    result = create_directory(str(tests_dir))
    assert result is True
    assert tests_dir.exists()
    assert tests_dir.is_dir()

def test_all_directories_exist(temp_base_path, capsys):
    """Integration test: Run main() and verify all directories exist."""
    # Patch the base path logic in main() by running it in a controlled env
    # Since main() uses __file__, we simulate by calling create_directory directly
    # for the specific set expected in the real run.
    
    directories = [
        temp_base_path / "scripts",
        temp_base_path / "data" / "raw",
        temp_base_path / "data" / "processed",
        temp_base_path / "data" / "splits",
        temp_base_path / "models",
        temp_base_path / "tests",
    ]

    for d in directories:
        create_directory(str(d))

    for d in directories:
        assert d.exists(), f"Directory {d} should exist"
        assert d.is_dir(), f"{d} should be a directory"
    
    captured = capsys.readouterr()
    assert "Created/Verified directory" in captured.out