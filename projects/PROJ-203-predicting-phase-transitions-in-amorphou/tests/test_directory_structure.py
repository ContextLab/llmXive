"""
Tests for T008: Directory Structure Setup.

Verifies that the required directories exist after running setup_directories.py.
"""

import os
import pytest
from pathlib import Path

# Locate project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"

# Expected directories relative to project root
EXPECTED_DIRS = [
    "data/raw",
    "data/processed",
    "data/logs",
    "models",
    "docs/reports",
    "docs/reports/shap_plots",
    "artifacts"
]

@pytest.fixture(scope="module", autouse=True)
def ensure_directories_exist():
    """
    Ensure directories exist before running tests.
    This simulates the execution of the setup task if not already run.
    """
    # We run the setup logic here to ensure the test environment is valid
    # In a real CI/CD, the setup script would be run as a pre-step.
    setup_script = CODE_DIR / "setup_directories.py"
    if setup_script.exists():
        import subprocess
        result = subprocess.run(
            ["python", str(setup_script)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        # We don't assert on the setup result here, just ensure we try.
        # The actual assertions are in the tests below.
    
    yield

def test_required_directories_exist():
    """Verify all required directories exist."""
    missing = []
    for dir_rel in EXPECTED_DIRS:
        full_path = PROJECT_ROOT / dir_rel
        if not full_path.exists():
            missing.append(dir_rel)
        elif not full_path.is_dir():
            missing.append(f"{dir_rel} (exists but is not a directory)")
    
    assert not missing, f"The following required directories are missing: {missing}"

def test_data_raw_is_writable():
    """Verify data/raw is writable."""
    test_file = PROJECT_ROOT / "data/raw" / ".test_write"
    try:
        test_file.touch()
        test_file.unlink()
        assert True
    except (OSError, IOError):
        pytest.fail("data/raw is not writable")

def test_models_directory_exists():
    """Verify models directory exists for saving artifacts."""
    models_path = PROJECT_ROOT / "models"
    assert models_path.exists()
    assert models_path.is_dir()

def test_docs_reports_exists():
    """Verify docs/reports directory exists."""
    reports_path = PROJECT_ROOT / "docs" / "reports"
    assert reports_path.exists()
    assert reports_path.is_dir()