"""
Tests for project setup and directory structure.
"""
import os
import sys
from pathlib import Path
import pytest
from tests.conftest import project_root

def test_code_directory_exists():
    """Verify that the code directory exists."""
    code_dir = project_root / "code"
    assert code_dir.exists(), f"Code directory {code_dir} does not exist"
    assert code_dir.is_dir(), f"{code_dir} is not a directory"

def test_src_directory_exists():
    """Verify that the src directory exists."""
    src_dir = project_root / "code" / "src"
    assert src_dir.exists(), f"Src directory {src_dir} does not exist"
    assert src_dir.is_dir(), f"{src_dir} is not a directory"

def test_tests_directory_exists():
    """Verify that the tests directory exists."""
    tests_dir = project_root / "code" / "tests"
    assert tests_dir.exists(), f"Tests directory {tests_dir} does not exist"
    assert tests_dir.is_dir(), f"{tests_dir} is not a directory"

def test_data_directory_exists():
    """Verify that the data directory exists."""
    data_dir = project_root / "code" / "data"
    assert data_dir.exists(), f"Data directory {data_dir} does not exist"
    assert data_dir.is_dir(), f"{data_dir} is not a directory"

def test_results_directory_exists():
    """Verify that the results directory exists."""
    results_dir = project_root / "code" / "results"
    assert results_dir.exists(), f"Results directory {results_dir} does not exist"
    assert results_dir.is_dir(), f"{results_dir} is not a directory"

def test_models_directory_exists():
    """Verify that the models directory exists."""
    models_dir = project_root / "code" / "models"
    assert models_dir.exists(), f"Models directory {models_dir} does not exist"
    assert models_dir.is_dir(), f"{models_dir} is not a directory"
