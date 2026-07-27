"""
Contract test for T001: Verify project structure exists.
"""
import os
from pathlib import Path
from config import (
    get_project_root,
    get_data_dir,
    get_raw_data_dir,
    get_processed_data_dir,
    get_consent_dir,
    get_specs_dir,
    get_contracts_dir,
    get_code_dir,
    get_tests_dir,
    get_figures_dir
)
import pytest

def test_core_directories_exist():
    """
    Verify that the core project directories exist.
    """
    required_dirs = [
        get_code_dir(),
        get_tests_dir(),
        get_specs_dir(),
        get_figures_dir(),
        get_data_dir(),
    ]

    for dir_path in required_dirs:
        path_obj = Path(dir_path)
        assert path_obj.exists(), f"Directory does not exist: {dir_path}"
        assert path_obj.is_dir(), f"Path is not a directory: {dir_path}"

def test_data_subdirectories_exist():
    """
    Verify that data subdirectories exist.
    """
    required_dirs = [
        get_raw_data_dir(),
        get_processed_data_dir(),
        get_consent_dir(),
    ]

    for dir_path in required_dirs:
        path_obj = Path(dir_path)
        assert path_obj.exists(), f"Directory does not exist: {dir_path}"
        assert path_obj.is_dir(), f"Path is not a directory: {dir_path}"

def test_contracts_directory_exists():
    """
    Verify that the contracts directory exists.
    """
    contracts_dir = get_contracts_dir()
    path_obj = Path(contracts_dir)
    assert path_obj.exists(), f"Directory does not exist: {contracts_dir}"
    assert path_obj.is_dir(), f"Path is not a directory: {contracts_dir}"

def test_package_init_files_exist():
    """
    Verify that __init__.py files exist for code and tests packages.
    """
    code_init = Path(get_code_dir()) / "__init__.py"
    tests_init = Path(get_tests_dir()) / "__init__.py"

    assert code_init.exists(), f"__init__.py missing in code/: {code_init}"
    assert tests_init.exists(), f"__init__.py missing in tests/: {tests_init}"