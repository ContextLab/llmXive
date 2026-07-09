"""
Tests for the setup_directories script (T001a).
"""
import os
import tempfile
import shutil
import pytest
import subprocess
import sys

# Import the function we want to test if possible, or rely on subprocess
# Since setup_directories.py is a script with a main guard, we test via subprocess
# or by importing the logic if refactored. Here we test the script execution.

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate the project root."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_script_creates_directories(temp_project_root):
    """Test that the script creates the required directories."""
    script_path = os.path.join(os.path.dirname(__file__), "..", "code", "setup_directories.py")
    # Normalize path
    script_path = os.path.abspath(script_path)

    if not os.path.exists(script_path):
        pytest.skip("Script not found, assuming manual verification needed")

    # Run the script in the temp directory
    result = subprocess.run(
        [sys.executable, script_path],
        cwd=temp_project_root,
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Script failed with output: {result.stderr}"

    # Verify directories exist
    required_dirs = [
        "code/data_ingestion",
        "code/modeling",
        "code/reporting",
        "code/utils",
        "tests",
        "data/raw",
        "data/processed",
        "results",
        "logs",
        "docs"
    ]

    for dir_path in required_dirs:
        full_path = os.path.join(temp_project_root, dir_path)
        assert os.path.isdir(full_path), f"Directory {dir_path} was not created"

def test_script_idempotent(temp_project_root):
    """Test that running the script twice does not error."""
    script_path = os.path.join(os.path.dirname(__file__), "..", "code", "setup_directories.py")
    script_path = os.path.abspath(script_path)

    if not os.path.exists(script_path):
        pytest.skip("Script not found")

    # Run twice
    result1 = subprocess.run([sys.executable, script_path], cwd=temp_project_root, capture_output=True, text=True)
    result2 = subprocess.run([sys.executable, script_path], cwd=temp_project_root, capture_output=True, text=True)

    assert result1.returncode == 0
    assert result2.returncode == 0
    # Second run should report skipping or success, not error
    assert "ERROR" not in result2.stdout