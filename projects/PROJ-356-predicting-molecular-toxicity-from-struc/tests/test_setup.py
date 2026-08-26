"""
Tests to verify the creation of the project directory structure.
These tests ensure that the required directories for PROJ-356 exist.
"""
import os
import sys
from pathlib import Path
import pytest

# Add the code directory to the path for imports if necessary,
# though this test primarily checks filesystem state.
from tests.conftest import project_root

def test_code_directory_exists():
    """Verify the root code directory exists."""
    # Expected path: projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/
    expected_path = project_root / "projects" / "PROJ-356-predicting-molecular-toxicity-from-struc" / "code"
    assert expected_path.exists(), f"Code directory does not exist: {expected_path}"
    assert expected_path.is_dir(), f"Path is not a directory: {expected_path}"

def test_src_directory_exists():
    """Verify the src directory exists."""
    expected_path = project_root / "projects" / "PROJ-356-predicting-molecular-toxicity-from-struc" / "code" / "src"
    assert expected_path.exists(), f"Src directory does not exist: {expected_path}"
    assert expected_path.is_dir(), f"Path is not a directory: {expected_path}"

def test_tests_directory_exists():
    """Verify the tests directory exists."""
    expected_path = project_root / "projects" / "PROJ-356-predicting-molecular-toxicity-from-struc" / "code" / "tests"
    assert expected_path.exists(), f"Tests directory does not exist: {expected_path}"
    assert expected_path.is_dir(), f"Path is not a directory: {expected_path}"

def test_data_directory_exists():
    """Verify the data directory exists."""
    expected_path = project_root / "projects" / "PROJ-356-predicting-molecular-toxicity-from-struc" / "code" / "data"
    assert expected_path.exists(), f"Data directory does not exist: {expected_path}"
    assert expected_path.is_dir(), f"Path is not a directory: {expected_path}"

def test_results_directory_exists():
    """Verify the results directory exists."""
    expected_path = project_root / "projects" / "PROJ-356-predicting-molecular-toxicity-from-struc" / "code" / "results"
    assert expected_path.exists(), f"Results directory does not exist: {expected_path}"
    assert expected_path.is_dir(), f"Path is not a directory: {expected_path}"

def test_models_directory_exists():
    """Verify the models directory exists."""
    expected_path = project_root / "projects" / "PROJ-356-predicting-molecular-toxicity-from-struc" / "code" / "models"
    assert expected_path.exists(), f"Models directory does not exist: {expected_path}"
    assert expected_path.is_dir(), f"Path is not a directory: {expected_path}"

def test_config_directory_exists():
    """Verify the config directory exists."""
    expected_path = project_root / "projects" / "PROJ-356-predicting-molecular-toxicity-from-struc" / "code" / "config"
    assert expected_path.exists(), f"Config directory does not exist: {expected_path}"
    assert expected_path.is_dir(), f"Path is not a directory: {expected_path}"

def test_docs_directory_exists():
    """Verify the docs directory exists."""
    expected_path = project_root / "projects" / "PROJ-356-predicting-molecular-toxicity-from-struc" / "docs"
    assert expected_path.exists(), f"Docs directory does not exist: {expected_path}"
    assert expected_path.is_dir(), f"Path is not a directory: {expected_path}"
