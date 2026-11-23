import os
import sys
from pathlib import Path
import pytest

def test_tests_directory_structure_exists():
    """
    Verifies that the tests directory hierarchy (tests/, tests/unit/, tests/integration/)
    exists and is writable.
    """
    # Determine project root (assuming tests/unit is at tests/unit/test_setup_verification.py)
    project_root = Path(__file__).resolve().parent.parent.parent
    tests_dir = project_root / "tests"
    unit_dir = tests_dir / "unit"
    integration_dir = tests_dir / "integration"

    # Check existence
    assert tests_dir.exists(), f"Directory {tests_dir} does not exist."
    assert unit_dir.exists(), f"Directory {unit_dir} does not exist."
    assert integration_dir.exists(), f"Directory {integration_dir} does not exist."

    # Check writability
    test_files = []
    try:
        for d in [tests_dir, unit_dir, integration_dir]:
            test_file = d / ".write_test_verify"
            with open(test_file, 'w') as f:
                f.write("verify")
            test_files.append(test_file)
            # Clean up
            os.remove(test_file)
    except PermissionError:
        pytest.fail("One or more test directories are not writable.")
    
    assert True, "All directories exist and are writable."

def test_setup_tests_script_runs():
    """
    Runs the setup_tests.py script to ensure it executes without error.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    script_path = project_root / "code" / "setup_tests.py"
    
    if not script_path.exists():
        pytest.skip("setup_tests.py not found, assuming environment is already set up.")
    
    # We can't easily run the script as a subprocess in this context without
    # potentially interfering with the test runner's environment, but we can
    # import and call the function directly.
    sys.path.insert(0, str(project_root))
    try:
        from setup_tests import setup_tests_directories
        result = setup_tests_directories()
        assert result is True, "setup_tests_directories() returned False."
    finally:
        sys.path.remove(str(project_root))