"""
Unit tests for environment setup verification.
These tests verify that the virtual environment was created correctly
and that required dependencies are installed.
"""
import os
import subprocess
import sys
import importlib.util
import pytest

# Path configuration relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VENV_PATH = os.path.join(PROJECT_ROOT, "venv")

@pytest.fixture
def venv_exists():
    """Check if the virtual environment directory exists."""
    return os.path.isdir(VENV_PATH)

@pytest.fixture
def pip_executable():
    """Return the path to the pip executable in the venv."""
    if sys.platform == "win32":
        return os.path.join(VENV_PATH, "Scripts", "pip.exe")
    else:
        return os.path.join(VENV_PATH, "bin", "pip")

def test_venv_directory_created(venv_exists):
    """Test that the virtual environment directory was created."""
    assert venv_exists, "Virtual environment directory 'venv' not found in project root."

def test_venv_python_executable_exists(venv_exists):
    """Test that the Python executable inside the venv exists."""
    if not venv_exists:
        pytest.skip("Virtual environment does not exist.")
    
    if sys.platform == "win32":
        python_path = os.path.join(VENV_PATH, "Scripts", "python.exe")
    else:
        python_path = os.path.join(VENV_PATH, "bin", "python")
    
    assert os.path.isfile(python_path), f"Python executable not found at {python_path}"

def test_required_packages_installed(pip_executable):
    """Test that required packages from requirements.txt are installed."""
    if not os.path.isfile(pip_executable):
        pytest.skip("Pip executable not found in venv.")

    required_packages = [
        "pandas",
        "scipy",
        "scikit-learn",
        "transformers",
        "pydantic",
        "pytest",
        "statsmodels"
    ]

    result = subprocess.run(
        [pip_executable, "list", "--format=freeze"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Failed to run pip list: {result.stderr}"

    installed_packages = {line.split("==")[0].lower() for line in result.stdout.splitlines()}

    missing_packages = []
    for package in required_packages:
        if package.lower() not in installed_packages:
            missing_packages.append(package)

    assert not missing_packages, f"Missing required packages in virtual environment: {missing_packages}"

def test_package_imports():
    """Test that we can actually import the required packages using the venv python."""
    if not os.path.isdir(VENV_PATH):
        pytest.skip("Virtual environment does not exist.")

    if sys.platform == "win32":
        python_exe = os.path.join(VENV_PATH, "Scripts", "python.exe")
    else:
        python_exe = os.path.join(VENV_PATH, "bin", "python")

    packages_to_test = [
        ("pandas", "pd"),
        ("scipy", "scipy"),
        ("scikit-learn", "sklearn"),
        ("transformers", "transformers"),
        ("pydantic", "pydantic"),
        ("pytest", "pytest"),
        ("statsmodels", "statsmodels")
    ]

    for package_name, import_name in packages_to_test:
        result = subprocess.run(
            [python_exe, "-c", f"import {import_name}"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Failed to import {package_name}: {result.stderr}"