"""
Test to verify that the project directory structure (T001) has been correctly created.
This test ensures that code/, data/, contracts/, and tests/ exist as required.
"""
import os
from pathlib import Path

def test_project_root_exists():
    """Verify the project root is accessible."""
    root = Path(__file__).parent.parent
    assert root.exists(), f"Project root {root} does not exist."

def test_code_directory_exists():
    """Verify code/ directory exists."""
    root = Path(__file__).parent.parent
    code_dir = root / "code"
    assert code_dir.exists(), f"Directory {code_dir} does not exist."
    assert code_dir.is_dir(), f"{code_dir} is not a directory."

def test_data_directory_exists():
    """Verify data/ directory and subdirectories exist."""
    root = Path(__file__).parent.parent
    data_dir = root / "data"
    assert data_dir.exists(), f"Directory {data_dir} does not exist."
    
    subdirs = ["raw", "processed", "logs", "figures"]
    for subdir in subdirs:
        sub_path = data_dir / subdir
        assert sub_path.exists(), f"Subdirectory {sub_path} does not exist."
        assert sub_path.is_dir(), f"{sub_path} is not a directory."

def test_contracts_directory_exists():
    """Verify contracts/ directory exists."""
    root = Path(__file__).parent.parent
    contracts_dir = root / "contracts"
    assert contracts_dir.exists(), f"Directory {contracts_dir} does not exist."
    assert contracts_dir.is_dir(), f"{contracts_dir} is not a directory."

def test_tests_directory_exists():
    """Verify tests/ directory exists."""
    root = Path(__file__).parent.parent
    tests_dir = root / "tests"
    assert tests_dir.exists(), f"Directory {tests_dir} does not exist."
    assert tests_dir.is_dir(), f"{tests_dir} is not a directory."

def test_schema_files_exist():
    """Verify contract schema files exist."""
    root = Path(__file__).parent.parent
    contracts_dir = root / "contracts"
    
    schema_files = ["dataset.schema.yaml", "output.schema.yaml"]
    for schema_file in schema_files:
        file_path = contracts_dir / schema_file
        assert file_path.exists(), f"Schema file {file_path} does not exist."

def test_config_module_imports():
    """Verify config.py exists and can be imported."""
    root = Path(__file__).parent.parent
    config_path = root / "code" / "config.py"
    assert config_path.exists(), f"Config file {config_path} does not exist."
    
    # Try to import to ensure it's valid Python
    import sys
    sys.path.insert(0, str(root / "code"))
    try:
        import config
        assert hasattr(config, 'ensure_directories'), "ensure_directories function missing in config"
        assert hasattr(config, 'get_config_dict'), "get_config_dict function missing in config"
    finally:
        sys.path.remove(str(root / "code"))