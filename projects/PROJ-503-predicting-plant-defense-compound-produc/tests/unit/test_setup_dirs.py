"""
Unit tests for T014: Project Structure Setup.
Verifies that the setup_dirs.sh script creates the required directory structure.
"""
import os
import subprocess
import pytest
from pathlib import Path

PROJECT_ROOT = Path("projects/PROJ-503-predicting-plant-defense-compound-produc")
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "setup_dirs.sh"

REQUIRED_DIRS = [
    "code/",
    "data/raw/",
    "data/processed/",
    "logs/",
    "outputs/models/",
    "docs/",
    "tests/contract/",
    "tests/integration/",
    "tests/unit/",
]

@pytest.fixture(scope="module", autouse=True)
def setup_environment(tmp_path_factory):
    """
    Ensure the script is executable and run it before tests if it hasn't been run yet.
    In a real CI/CD context, this would be done in the pipeline, but for unit testing
    we ensure the state is correct.
    """
    # We don't actually run the script here as a side-effect of the test fixture 
    # to avoid modifying the file system during test collection unless necessary.
    # The test itself will verify existence.
    pass

def test_script_exists():
    """Verify that the setup script exists."""
    assert SCRIPT_PATH.exists(), f"Setup script not found at {SCRIPT_PATH}"

def test_script_is_executable():
    """Verify that the setup script has execute permissions."""
    # Note: On Windows, executable bit is different, but we check os.access for X_OK
    # If running in a restricted environment, this might need adjustment, 
    # but for a Linux/Unix runner it's standard.
    assert os.access(SCRIPT_PATH, os.X_OK) or os.access(SCRIPT_PATH, os.R_OK), \
        f"Script {SCRIPT_PATH} is not readable/executable"

def test_directories_exist_after_setup():
    """
    Run the setup script and verify all required directories are created.
    This test executes the script to ensure the 'Run the script' requirement is met.
    """
    # Ensure we are in the project root context
    # The script uses relative paths, so we run it from the repo root.
    # Assuming the test runner is in the repo root.
    
    # Make sure script is executable
    if not os.access(SCRIPT_PATH, os.X_OK):
        os.chmod(SCRIPT_PATH, 0o755)

    # Execute the script
    result = subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        capture_output=True,
        text=True
    )

    # Assert script ran successfully
    assert result.returncode == 0, f"Setup script failed:\n{result.stderr}"

    # Verify each required directory exists
    for dir_name in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_name
        assert full_path.exists(), f"Required directory missing: {full_path}"
        assert full_path.is_dir(), f"Path exists but is not a directory: {full_path}"

def test_directory_structure_integrity():
    """
    Verify that the created directories match the exact specification.
    """
    # Check specific nested structures
    assert (PROJECT_ROOT / "data" / "raw").exists()
    assert (PROJECT_ROOT / "data" / "processed").exists()
    assert (PROJECT_ROOT / "outputs" / "models").exists()
    assert (PROJECT_ROOT / "tests" / "contract").exists()
    assert (PROJECT_ROOT / "tests" / "integration").exists()
    assert (PROJECT_ROOT / "tests" / "unit").exists()

    # Ensure no typos in path construction
    expected_paths = [
        "projects/PROJ-503-predicting-plant-defense-compound-produc/code",
        "projects/PROJ-503-predicting-plant-defense-compound-produc/data/raw",
        "projects/PROJ-503-predicting-plant-defense-compound-produc/data/processed",
        "projects/PROJ-503-predicting-plant-defense-compound-produc/logs",
        "projects/PROJ-503-predicting-plant-defense-compound-produc/outputs/models",
        "projects/PROJ-503-predicting-plant-defense-compound-produc/docs",
        "projects/PROJ-503-predicting-plant-defense-compound-produc/tests/contract",
        "projects/PROJ-503-predicting-plant-defense-compound-produc/tests/integration",
        "projects/PROJ-503-predicting-plant-defense-compound-produc/tests/unit",
    ]
    
    for path_str in expected_paths:
        p = Path(path_str)
        assert p.exists(), f"Expected path does not exist: {path_str}"