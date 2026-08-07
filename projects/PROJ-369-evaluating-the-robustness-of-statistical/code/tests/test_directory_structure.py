import pytest
from pathlib import Path
import os
from src.utils.config import get_path

def test_required_directories_exist():
    """
    Test that the required project directories exist at the repository root.
    This validates the outcome of T001, T001b, T001c, and T001d.
    """
    root = get_path("")
    
    # T001: src directory
    src_dir = root / "src"
    assert src_dir.exists(), f"Directory 'src' does not exist at {src_dir}"
    assert src_dir.is_dir(), f"'src' is not a directory"
    
    # T001b: tests directory
    tests_dir = root / "tests"
    assert tests_dir.exists(), f"Directory 'tests' does not exist at {tests_dir}"
    assert tests_dir.is_dir(), f"'tests' is not a directory"
    
    # T001c: data, results, specs directories
    data_dir = root / "data"
    assert data_dir.exists(), f"Directory 'data' does not exist at {data_dir}"
    assert data_dir.is_dir(), f"'data' is not a directory"
    
    results_dir = root / "results"
    assert results_dir.exists(), f"Directory 'results' does not exist at {results_dir}"
    assert results_dir.is_dir(), f"'results' is not a directory"
    
    specs_dir = root / "specs"
    assert specs_dir.exists(), f"Directory 'specs' does not exist at {specs_dir}"
    assert specs_dir.is_dir(), f"'specs' is not a directory"
    
    # T001d: data/raw and data/processed subdirectories
    raw_dir = root / "data" / "raw"
    assert raw_dir.exists(), f"Directory 'data/raw' does not exist at {raw_dir}"
    assert raw_dir.is_dir(), f"'data/raw' is not a directory"
    
    processed_dir = root / "data" / "processed"
    assert processed_dir.exists(), f"Directory 'data/processed' does not exist at {processed_dir}"
    assert processed_dir.is_dir(), f"'data/processed' is not a directory"

def test_directory_setup_script_exists():
    """
    Verify that the script responsible for setting up directories exists.
    """
    root = get_path("")
    setup_script = root / "code" / "run_directory_setup.py"
    assert setup_script.exists(), f"Setup script not found at {setup_script}"