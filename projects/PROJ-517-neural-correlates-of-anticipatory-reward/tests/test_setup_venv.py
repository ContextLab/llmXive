"""
Tests for the virtual environment setup script.
These tests verify that the setup script creates the necessary structure
and can be executed without error.
"""
import os
import subprocess
import sys
from pathlib import Path
import pytest

@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent

@pytest.fixture
def requirements_path(project_root):
    """Return the path to requirements.txt."""
    return project_root / "projects" / "PROJ-517-neural-correlates-of-anticipatory-reward" / "requirements.txt"

@pytest.fixture
def venv_path(project_root):
    """Return the path to the virtual environment."""
    return project_root / ".venv"

def test_requirements_file_exists(project_root, requirements_path):
    """Test that requirements.txt exists and contains expected packages."""
    assert requirements_path.exists(), "requirements.txt should exist"
    
    content = requirements_path.read_text()
    expected_packages = [
        "pandas", "numpy", "scipy", "statsmodels", 
        "scikit-learn", "matplotlib", "seaborn", "pyyaml", "pytest"
    ]
    
    for package in expected_packages:
        assert package.lower() in content.lower(), f"{package} should be in requirements.txt"

def test_setup_script_exists(project_root):
    """Test that the setup script exists."""
    setup_script = project_root / "code" / "setup_venv.py"
    assert setup_script.exists(), "setup_venv.py should exist"

def test_setup_script_syntax(project_root):
    """Test that the setup script has valid Python syntax."""
    setup_script = project_root / "code" / "setup_venv.py"
    try:
        compile(setup_script.read_text(), setup_script, 'exec')
    except SyntaxError as e:
        pytest.fail(f"setup_venv.py has syntax errors: {e}")

@pytest.mark.integration
def test_venv_creation(project_root, venv_path, requirements_path):
    """Test that the virtual environment can be created and dependencies installed."""
    # Skip if venv already exists to avoid re-running in CI unless forced
    if venv_path.exists():
        pytest.skip("Virtual environment already exists")

    # Run the setup script
    result = subprocess.run(
        [sys.executable, str(project_root / "code" / "setup_venv.py")],
        capture_output=True,
        text=True
    )
    
    # Check for success
    assert result.returncode == 0, f"Setup script failed: {result.stderr}"
    
    # Verify venv directory was created
    assert venv_path.exists(), "Virtual environment directory should be created"
    
    # Verify pip exists in venv
    if sys.platform == "win32":
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:
        pip_path = venv_path / "bin" / "pip"
        
    assert pip_path.exists(), "pip should exist in virtual environment"