"""
Utility script to verify pytest framework setup and directory structure.
Run this to ensure the test environment is correctly initialized.
"""
import os
import sys
from pathlib import Path

def verify_test_structure():
    """Verify that the pytest directory structure exists."""
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    unit_dir = tests_dir / "unit"
    integration_dir = tests_dir / "integration"
    conftest = tests_dir / "conftest.py"
    pytest_ini = project_root / "pytest.ini"

    checks = [
        (tests_dir.exists(), "tests/ directory exists"),
        (unit_dir.exists(), "tests/unit/ directory exists"),
        (integration_dir.exists(), "tests/integration/ directory exists"),
        (conftest.exists(), "tests/conftest.py exists"),
        (pytest_ini.exists(), "pytest.ini exists"),
    ]

    all_passed = True
    for passed, message in checks:
        status = "✓" if passed else "✗"
        print(f"{status} {message}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n✓ Pytest framework and directory structure are correctly set up.")
        return 0
    else:
        print("\n✗ Verification failed. Please check the directory structure.")
        return 1

if __name__ == "__main__":
    sys.exit(verify_test_structure())