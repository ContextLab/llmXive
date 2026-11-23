import os
from pathlib import Path

def test_tests_root_exists():
    """Verify that the tests directory exists at the project root."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    tests_root = base_dir / "tests"
    assert tests_root.exists(), f"Tests directory not found at {tests_root}"
    assert tests_root.is_dir(), f"{tests_root} is not a directory"

def test_unit_directory_exists():
    """Verify that tests/unit/ exists."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    unit_dir = base_dir / "tests" / "unit"
    assert unit_dir.exists(), f"Unit test directory not found at {unit_dir}"
    assert unit_dir.is_dir(), f"{unit_dir} is not a directory"

def test_integration_directory_exists():
    """Verify that tests/integration/ exists."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    integration_dir = base_dir / "tests" / "integration"
    assert integration_dir.exists(), f"Integration test directory not found at {integration_dir}"
    assert integration_dir.is_dir(), f"{integration_dir} is not a directory"

def test_contract_directory_exists():
    """Verify that tests/contract/ exists."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    contract_dir = base_dir / "tests" / "contract"
    assert contract_dir.exists(), f"Contract test directory not found at {contract_dir}"
    assert contract_dir.is_dir(), f"{contract_dir} is not a directory"

def test_data_directory_structure():
    """Verify that data/raw, data/interim, data/processed, data/external exist."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_subdirs = ["raw", "interim", "processed", "external"]
    
    for subdir in data_subdirs:
        dir_path = base_dir / "data" / subdir
        assert dir_path.exists(), f"Data directory {subdir} not found at {dir_path}"
        assert dir_path.is_dir(), f"{dir_path} is not a directory"
