import os
import pytest
from pathlib import Path

def test_code_directory_structure():
    """
    Test that the code directory structure required by T001a exists.
    """
    project_root = Path(__file__).parent.parent.parent
    code_base = project_root / "code"
    
    required_dirs = [
        "code",
        "code/data",
        "code/models",
        "code/eval",
        "code/utils"
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Directory missing: {full_path}"
        assert full_path.is_dir(), f"Not a directory: {full_path}"

def test_data_directory_structure():
    """
    Test that the data directory structure required by T001b exists.
    """
    project_root = Path(__file__).parent.parent.parent
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/splits",
        "data/schemas"
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Directory missing: {full_path}"
        assert full_path.is_dir(), f"Not a directory: {full_path}"

def test_tests_directory_structure():
    """
    Test that the tests directory structure required by T001c exists.
    """
    project_root = Path(__file__).parent.parent.parent
    
    required_dirs = [
        "tests/contract",
        "tests/unit",
        "tests/integration"
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Directory missing: {full_path}"
        assert full_path.is_dir(), f"Not a directory: {full_path}"

def test_results_directory_structure():
    """
    Test that the results directory structure required by T001d exists.
    """
    project_root = Path(__file__).parent.parent.parent
    
    required_dirs = [
        "results/reports",
        "results/plots"
    ]
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Directory missing: {full_path}"
        assert full_path.is_dir(), f"Not a directory: {full_path}"