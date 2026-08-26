"""
Tests to verify that the project directory structure is correctly created.
"""
import os
import sys
from pathlib import Path
import pytest
from tests.conftest import project_root

def test_code_directory_exists():
    """Verify the main code directory exists."""
    code_dir = project_root / "code"
    assert code_dir.exists(), f"Code directory {code_dir} does not exist"
    assert code_dir.is_dir(), f"{code_dir} is not a directory"

def test_src_directory_exists():
    """Verify the src directory exists."""
    src_dir = project_root / "code" / "src"
    assert src_dir.exists(), f"Src directory {src_dir} does not exist"
    assert src_dir.is_dir(), f"{src_dir} is not a directory"

def test_tests_directory_exists():
    """Verify the tests directory exists (current task)."""
    tests_dir = project_root / "code" / "tests"
    assert tests_dir.exists(), f"Tests directory {tests_dir} does not exist"
    assert tests_dir.is_dir(), f"{tests_dir} is not a directory"
    # Verify it contains at least an __init__.py or conftest.py
    has_init = (tests_dir / "__init__.py").exists()
    has_conftest = (tests_dir / "conftest.py").exists()
    assert has_init or has_conftest, f"Tests directory {tests_dir} is empty"

def test_data_directory_exists():
    """Verify the data directory exists."""
    data_dir = project_root / "code" / "data"
    assert data_dir.exists(), f"Data directory {data_dir} does not exist"
    assert data_dir.is_dir(), f"{data_dir} is not a directory"

def test_results_directory_exists():
    """Verify the results directory exists."""
    results_dir = project_root / "code" / "results"
    assert results_dir.exists(), f"Results directory {results_dir} does not exist"
    assert results_dir.is_dir(), f"{results_dir} is not a directory"

def test_models_directory_exists():
    """Verify the models directory exists."""
    models_dir = project_root / "code" / "models"
    assert models_dir.exists(), f"Models directory {models_dir} does not exist"
    assert models_dir.is_dir(), f"{models_dir} is not a directory"

def test_config_directory_exists():
    """Verify the config directory exists."""
    config_dir = project_root / "code" / "config"
    assert config_dir.exists(), f"Config directory {config_dir} does not exist"
    assert config_dir.is_dir(), f"{config_dir} is not a directory"

def test_docs_directory_exists():
    """Verify the docs directory exists."""
    docs_dir = project_root / "docs"
    assert docs_dir.exists(), f"Docs directory {docs_dir} does not exist"
    assert docs_dir.is_dir(), f"{docs_dir} is not a directory"
