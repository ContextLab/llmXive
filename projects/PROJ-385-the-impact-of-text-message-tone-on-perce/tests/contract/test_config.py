"""
Contract tests for the configuration module (T007).

Verifies that:
1. RANDOM_SEED is an integer.
2. BASE_DATA_PATH points to 'data'.
3. Path resolution functions return valid Path objects under the project root.
"""
import pytest
from pathlib import Path

from config import (
    RANDOM_SEED,
    BASE_DATA_PATH_STR,
    get_project_root,
    get_data_dir,
    get_raw_data_dir,
    get_processed_data_dir,
    get_consent_dir,
    get_results_dir,
    get_specs_dir,
    get_contracts_dir,
    get_figures_dir,
    get_code_dir,
    get_tests_dir,
)


def test_random_seed_is_integer():
    """Verify RANDOM_SEED is an integer."""
    assert isinstance(RANDOM_SEED, int), f"RANDOM_SEED must be an integer, got {type(RANDOM_SEED)}"


def test_base_data_path_is_data():
    """Verify BASE_DATA_PATH points to 'data'."""
    assert BASE_DATA_PATH_STR == "data", f"BASE_DATA_PATH must be 'data', got '{BASE_DATA_PATH_STR}'"


def test_get_project_root_returns_path():
    """Verify get_project_root returns a Path object."""
    root = get_project_root()
    assert isinstance(root, Path), f"get_project_root must return a Path, got {type(root)}"
    assert root.exists(), "Project root path must exist"


def test_get_data_dir_points_to_data():
    """Verify get_data_dir returns a path ending in 'data'."""
    data_dir = get_data_dir()
    assert data_dir.name == "data", f"get_data_dir must return a path named 'data', got {data_dir.name}"
    # It should be under the project root
    assert data_dir.parent == get_project_root()


def test_subdirs_are_under_data():
    """Verify all data subdirectories are under the data directory."""
    root = get_project_root()
    data_root = get_data_dir()

    assert get_raw_data_dir().parent == data_root
    assert get_processed_data_dir().parent == data_root
    assert get_consent_dir().parent == data_root
    assert get_results_dir().parent == data_root
    assert get_figures_dir().parent == data_root


def test_specs_and_contracts_exist_or_are_resolvable():
    """Verify specs and contracts paths resolve relative to root."""
    specs = get_specs_dir()
    contracts = get_contracts_dir()

    assert specs.parent == root
    assert contracts.parent == specs
    # We don't assert existence of the specific folder if it doesn't exist yet,
    # but we assert the path resolution logic is correct.
    assert contracts.name == "contracts"


def test_code_and_tests_dirs():
    """Verify code and tests directories resolve correctly."""
    root = get_project_root()
    assert get_code_dir() == root / "code"
    assert get_tests_dir() == root / "tests"