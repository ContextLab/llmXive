"""
Placeholder test to verify pytest configuration is working.
This test should pass if pytest is correctly configured.
"""
import pytest

def test_pytest_configuration():
    """
    Simple test to verify the test environment is set up correctly.
    """
    assert True, "Pytest configuration is working."

def test_directory_structure_exists():
    """
    Verify that expected directory structures exist in the test environment.
    """
    import os
    from pathlib import Path
    
    # Check for standard directories
    expected_dirs = [
        "tests/unit",
        "tests/integration", 
        "tests/contract"
    ]
    
    for dir_path in expected_dirs:
        full_path = Path(__file__).parent.parent / dir_path
        assert full_path.exists(), f"Directory {dir_path} does not exist"
        assert full_path.is_dir(), f"{dir_path} is not a directory"

def test_imports_work():
    """
    Verify that key modules can be imported from the test environment.
    """
    try:
        from code.src.utils.config import get_project_root, set_global_seed
        from code.src.data.synthetic_gen import generate_synthetic_cohort
        assert True, "Imports are working correctly"
    except ImportError as e:
        pytest.fail(f"Import error: {e}")