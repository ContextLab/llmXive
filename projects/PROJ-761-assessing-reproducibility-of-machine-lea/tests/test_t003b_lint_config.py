"""
Test to verify that linting and formatting configurations are valid.
This test ensures that ruff and black can successfully parse the project
structure and that the configuration files are correctly set up.
"""
import os
import subprocess
import tempfile
import shutil

def test_ruff_config_exists():
    """Verify ruff configuration is present in pyproject.toml."""
    # Check if pyproject.toml exists and contains ruff config
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pyproject_path = os.path.join(project_root, "pyproject.toml")
    
    assert os.path.exists(pyproject_path), "pyproject.toml must exist"
    
    with open(pyproject_path, 'r') as f:
        content = f.read()
    
    assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff] section"
    assert "line-length" in content, "pyproject.toml must contain line-length configuration"
    assert "target-version" in content, "pyproject.toml must contain target-version configuration"

def test_black_config_exists():
    """Verify black configuration is present in pyproject.toml."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pyproject_path = os.path.join(project_root, "pyproject.toml")
    
    assert os.path.exists(pyproject_path), "pyproject.toml must exist"
    
    with open(pyproject_path, 'r') as f:
        content = f.read()
    
    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"
    assert "line-length" in content, "pyproject.toml must contain line-length configuration"

def test_project_structure_exists():
    """Verify that the required project directories exist."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts/logs",
        "artifacts/plots",
        "artifacts/reports",
        "contracts"
    ]
    
    for dir_path in required_dirs:
        full_path = os.path.join(project_root, dir_path)
        assert os.path.isdir(full_path), f"Required directory {dir_path} must exist"

def test_ruff_can_check_project():
    """Verify that ruff can successfully run on the project."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        result = subprocess.run(
            ["ruff", "check", "code/", "tests/"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        # Ruff should be able to run without configuration errors
        # Exit code 0 means no issues, 1 means issues found (but config is valid)
        # We only care that it doesn't fail with a config error
        assert result.returncode in [0, 1], f"Ruff check failed with unexpected error: {result.stderr}"
    except subprocess.TimeoutExpired:
        raise AssertionError("Ruff check timed out")
    except FileNotFoundError:
        raise AssertionError("Ruff is not installed or not in PATH")

def test_black_can_check_project():
    """Verify that black can successfully run on the project."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        result = subprocess.run(
            ["black", "--check", "code/", "tests/"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        # Black should be able to run without configuration errors
        # Exit code 0 means formatted correctly, 1 means formatting needed
        # We only care that it doesn't fail with a config error
        assert result.returncode in [0, 1], f"Black check failed with unexpected error: {result.stderr}"
    except subprocess.TimeoutExpired:
        raise AssertionError("Black check timed out")
    except FileNotFoundError:
        raise AssertionError("Black is not installed or not in PATH")
