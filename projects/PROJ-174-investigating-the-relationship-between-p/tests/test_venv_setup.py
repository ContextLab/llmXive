"""
Test for Task T002b: Verify Python 3.11 virtual environment setup.

This test verifies that:
1. The virtual environment directory exists at code/.venv
2. The python executable in the venv is version 3.11
3. Dependencies from requirements.txt are installed
"""
import subprocess
import sys
import os
from pathlib import Path
import pytest

# Project root is the parent of the tests/ directory
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
VENV_DIR = CODE_DIR / ".venv"

def test_venv_directory_exists():
    """Test that the virtual environment directory exists."""
    assert VENV_DIR.exists(), f"Virtual environment directory not found: {VENV_DIR}"
    assert VENV_DIR.is_dir(), f"{VENV_DIR} is not a directory"

def test_venv_python_executable_exists():
    """Test that the Python executable exists in the virtual environment."""
    if os.name == 'nt':  # Windows
        python_exec = VENV_DIR / "Scripts" / "python.exe"
    else:  # Unix/Linux/Mac
        python_exec = VENV_DIR / "bin" / "python"
    
    assert python_exec.exists(), f"Python executable not found: {python_exec}"
    assert python_exec.is_file(), f"{python_exec} is not a file"

def test_venv_python_version_is_3_11():
    """Test that the virtual environment uses Python 3.11."""
    if os.name == 'nt':  # Windows
        python_exec = VENV_DIR / "Scripts" / "python.exe"
    else:  # Unix/Linux/Mac
        python_exec = VENV_DIR / "bin" / "python"
    
    result = subprocess.run(
        [str(python_exec), "--version"],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    assert result.returncode == 0, f"Failed to get Python version: {result.stderr}"
    
    version_output = result.stderr.strip() if result.stderr else result.stdout.strip()
    
    # Check that version contains '3.11'
    assert '3.11' in version_output, (
        f"Virtual environment does not use Python 3.11. "
        f"Found: {version_output}"
    )

def test_requirements_file_exists():
    """Test that requirements.txt exists in the code directory."""
    requirements_file = CODE_DIR / "requirements.txt"
    assert requirements_file.exists(), f"Requirements file not found: {requirements_file}"
    assert requirements_file.is_file(), f"{requirements_file} is not a file"

def test_basic_dependencies_installed():
    """Test that basic dependencies from requirements.txt are installed."""
    if os.name == 'nt':  # Windows
        python_exec = VENV_DIR / "Scripts" / "python.exe"
        pip_exec = VENV_DIR / "Scripts" / "pip.exe"
    else:  # Unix/Linux/Mac
        python_exec = VENV_DIR / "bin" / "python"
        pip_exec = VENV_DIR / "bin" / "pip"
    
    # Read requirements
    requirements_file = CODE_DIR / "requirements.txt"
    with open(requirements_file, 'r') as f:
        requirements = [
            line.strip().split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0]
            for line in f
            if line.strip() and not line.startswith('#')
        ]
    
    # Check if at least one key dependency is installed
    key_packages = ['pandas', 'numpy', 'scipy', 'requests']
    installed_packages = []
    
    for pkg in key_packages:
        if pkg in requirements:
            result = subprocess.run(
                [str(pip_exec), "show", pkg],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                installed_packages.append(pkg)
    
    # At least one key package should be installed
    assert len(installed_packages) > 0, (
        f"No key dependencies found installed. "
        f"Expected at least one of: {key_packages}"
    )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])