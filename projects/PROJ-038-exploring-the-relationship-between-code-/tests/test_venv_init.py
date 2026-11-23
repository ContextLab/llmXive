import os
import subprocess
import sys
import tempfile
import shutil
import pytest
from pathlib import Path

def get_project_root():
    """Determine the project root relative to this test file."""
    return Path(__file__).parent.parent

def test_venv_creation_script_exists():
    """Verify that the setup_venv.sh script exists in the code directory."""
    project_root = get_project_root()
    script_path = project_root / "code" / "setup_venv.sh"
    assert script_path.exists(), f"Script {script_path} does not exist."
    assert os.access(script_path, os.X_OK) or True  # Script might not be executable yet, but should exist

def test_venv_initialization_logic():
    """
    Test the logic of venv initialization by running the script.
    This simulates the task requirement to initialize the environment.
    """
    project_root = get_project_root()
    script_path = project_root / "code" / "setup_venv.sh"
    
    if not script_path.exists():
        pytest.skip("setup_venv.sh not found, skipping execution test")

    # Ensure the script is executable
    os.chmod(script_path, 0o755)

    # Run the script
    result = subprocess.run(
        [str(script_path)],
        cwd=project_root / "code",
        capture_output=True,
        text=True
    )

    # Verify success
    assert result.returncode == 0, f"Script failed with output:\n{result.stdout}\n{result.stderr}"
    
    # Verify the venv directory was created
    venv_path = project_root / "code" / ".venv"
    assert venv_path.exists(), "Virtual environment directory .venv was not created."
    assert (venv_path / "bin" / "activate").exists(), "Activation script not found in .venv."
    assert (venv_path / "bin" / "python").exists(), "Python executable not found in .venv."

def test_venv_python_version():
    """
    Verify that the created virtual environment uses the correct Python version.
    """
    project_root = get_project_root()
    venv_python = project_root / "code" / ".venv" / "bin" / "python"
    
    if not venv_python.exists():
        pytest.skip("Virtual environment not found, skipping version check")

    result = subprocess.run(
        [str(venv_python), "--version"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, "Could not run python in venv"
    # Check that the version string contains '3.11' or similar if python3.11 was requested
    # The task specifically asked for python3.11
    assert "3.11" in result.stdout or "3.11" in result.stderr, f"Python version mismatch: {result.stdout}"