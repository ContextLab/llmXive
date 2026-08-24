"""
Pytest configuration and shared fixtures.
Ensures the tests directory structure is valid before running tests.
"""
import os
import pytest
from pathlib import Path

@pytest.fixture(scope="session", autouse=True)
def verify_test_structure(tmp_path_factory):
    """
    Verify that the tests directory hierarchy exists and is writable.
    This is a session-scoped fixture that runs once at the start.
    """
    tests_root = Path(__file__).parent
    unit_dir = tests_root / "unit"
    integration_dir = tests_root / "integration"
    
    assert tests_root.exists(), "tests/ directory does not exist"
    assert unit_dir.exists(), "tests/unit/ directory does not exist"
    assert integration_dir.exists(), "tests/integration/ directory does not exist"
    
    # Verify writability
    test_marker = unit_dir / ".pytest_marker"
    try:
        with open(test_marker, 'w') as f:
            f.write("ok")
        test_marker.unlink()
    except IOError:
        pytest.fail(f"tests/unit/ directory is not writable")
        
    test_marker = integration_dir / ".pytest_marker"
    try:
        with open(test_marker, 'w') as f:
            f.write("ok")
        test_marker.unlink()
    except IOError:
        pytest.fail(f"tests/integration/ directory is not writable")
        
    yield
