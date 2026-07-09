"""
Tests for T002b: Virtual Environment Setup.

This test suite verifies that the setup script correctly creates a virtual
environment and installs the required dependencies.
"""
import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure mimicking the project root."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        code_dir = root / "code"
        code_dir.mkdir()
        
        # Create a minimal requirements.txt
        req_file = root / "requirements.txt"
        req_file.write_text("requests\nnumpy\n")
        
        yield root
        
        # Cleanup handled by TemporaryDirectory

def test_venv_creation_and_install(temp_project_root):
    """
    Test that setup_venv.py creates a venv and installs packages.
    
    This test:
    1. Copies the setup script to the temp project.
    2. Runs the script.
    3. Verifies the venv directory exists.
    4. Verifies the installed packages (requests, numpy) are present.
    """
    # Locate the real setup script
    real_script = Path(__file__).parent.parent / "code" / "setup_venv.py"
    if not real_script.exists():
        pytest.skip("setup_venv.py not found in code/ directory")
    
    # Copy script to temp location
    temp_script = temp_project_root / "code" / "setup_venv.py"
    shutil.copy(real_script, temp_script)
    
    venv_path = temp_project_root / "venv"
    pip_executable = venv_path / "bin" / "pip" if os.name != "nt" else venv_path / "Scripts" / "pip.exe"
    python_executable = venv_path / "bin" / "python" if os.name != "nt" else venv_path / "Scripts" / "python.exe"

    # Run the script
    result = subprocess.run(
        [sys.executable, str(temp_script)],
        cwd=temp_project_root,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Setup script failed: {result.stderr}"
    
    # Check venv exists
    assert venv_path.exists(), "Virtual environment directory was not created"
    assert pip_executable.exists(), "pip executable not found in venv"
    assert python_executable.exists(), "python executable not found in venv"
    
    # Check installed packages
    check_result = subprocess.run(
        [str(pip_executable), "list"],
        capture_output=True,
        text=True
    )
    
    assert check_result.returncode == 0
    output = check_result.stdout.lower()
    assert "requests" in output, "Package 'requests' not found in installed packages"
    assert "numpy" in output, "Package 'numpy' not found in installed packages"