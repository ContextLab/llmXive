import os
import shutil
import tempfile
import pytest
import subprocess
import sys

@pytest.fixture
def project_root():
    """Create a temporary directory acting as the project root."""
    original_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)


def test_full_script_execution_creates_figures_dir(project_root):
    """
    Integration test: Run the script as a subprocess and verify
    that results/figures/ is created on disk.
    """
    # Ensure we are in the temp project root
    assert os.getcwd() == project_root

    # Run the script
    result = subprocess.run(
        [sys.executable, "code/create_results_dirs.py"],
        capture_output=True,
        text=True
    )

    # Check exit code
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify artifacts exist
    assert os.path.exists("results"), "Directory 'results' was not created."
    assert os.path.exists("results/figures"), "Directory 'results/figures' was not created."

    # Verify they are directories
    assert os.path.isdir("results")
    assert os.path.isdir("results/figures")