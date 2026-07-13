"""
Integration test to verify the setup script runs successfully.
"""
import os
import subprocess
import pytest

@pytest.fixture(scope="module")
def setup_output():
    """Run the setup script and capture output."""
    result = subprocess.run(
        ["python", "code/setup_project_structure.py"],
        capture_output=True,
        text=True,
        cwd=os.getcwd()
    )
    return result

def test_setup_script_runs(setup_output):
    """Test that the setup script runs without errors."""
    assert setup_output.returncode == 0, \
        f"Setup script failed with return code {setup_output.returncode}\n{setup_output.stderr}"

def test_setup_script_creates_directories(setup_output):
    """Test that the setup script creates all required directories."""
    required_dirs = [
        "code",
        "code/scheduler",
        "code/training",
        "code/analysis",
        "code/utils",
        "data/raw",
        "data/processed",
        "data/validation",
        "tests/unit",
        "tests/integration",
        "contracts",
    ]
    
    missing_dirs = [d for d in required_dirs if not os.path.isdir(d)]
    assert not missing_dirs, \
        f"Setup script did not create all required directories. Missing: {missing_dirs}"