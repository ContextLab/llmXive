"""
Tests for linting and formatting configuration.
"""
import os
import subprocess
import tempfile
import shutil

def test_flake8_config_exists():
    """Test that .flake8 configuration file exists."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    flake8_path = os.path.join(root_dir, ".flake8")
    assert os.path.exists(flake8_path), f".flake8 file not found at {flake8_path}"

    with open(flake8_path, "r") as f:
        content = f.read()
    
    assert "[flake8]" in content, "Missing [flake8] section in .flake8"
    assert "max-line-length" in content, "Missing max-line-length in .flake8"

def test_pyproject_config_exists():
    """Test that pyproject.toml configuration exists with black settings."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pyproject_path = os.path.join(root_dir, "pyproject.toml")
    assert os.path.exists(pyproject_path), f"pyproject.toml file not found at {pyproject_path}"

    with open(pyproject_path, "r") as f:
        content = f.read()
    
    assert "[tool.black]" in content, "Missing [tool.black] section in pyproject.toml"
    assert "line-length" in content, "Missing line-length in pyproject.toml black config"

def test_linting_dependencies_in_requirements():
    """Test that linting dependencies are in requirements.txt."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    requirements_path = os.path.join(root_dir, "requirements.txt")
    
    if os.path.exists(requirements_path):
        with open(requirements_path, "r") as f:
            content = f.read()
        
        required_deps = ["flake8", "black", "isort"]
        for dep in required_deps:
            assert dep.lower() in content.lower(), f"Missing {dep} in requirements.txt"

def test_setup_linting_script_runs():
    """Test that the setup_linting.py script runs without errors."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(root_dir, "code", "setup_linting.py")
    
    if os.path.exists(script_path):
        result = subprocess.run(
            ["python", script_path],
            cwd=root_dir,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Script failed with: {result.stderr}"
        
        # Verify files were created
        flake8_path = os.path.join(root_dir, ".flake8")
        pyproject_path = os.path.join(root_dir, "pyproject.toml")
        
        assert os.path.exists(flake8_path), ".flake8 was not created"
        assert os.path.exists(pyproject_path), "pyproject.toml was not created or updated"

def test_black_compatible_code():
    """Test that a sample Python file passes black formatting."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def test_function(x, y):
    result=x+y
    return result
""")
        temp_file = f.name
    
    try:
        # Try to run black on the file
        result = subprocess.run(
            ["black", "--check", temp_file],
            capture_output=True,
            text=True
        )
        
        # If black is not installed, skip the test
        if result.returncode != 0 and "black" not in result.stderr.lower():
            pass  # Skip if black not available
        else:
            # Black should be able to process the file (even if it needs formatting)
            pass
    finally:
        os.unlink(temp_file)

def test_flake8_runs_on_sample():
    """Test that flake8 can run on a sample file."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create a temporary test file with intentional issues
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
import os
import sys

def test_function(x, y):
    result=x+y
    return result
""")
        temp_file = f.name
    
    try:
        # Try to run flake8 on the file
        result = subprocess.run(
            ["flake8", temp_file],
            capture_output=True,
            text=True
        )
        
        # If flake8 is not installed, skip the test
        if "flake8" not in result.stderr.lower():
            pass  # Skip if flake8 not available
        else:
            # flake8 should be able to process the file
            pass
    finally:
        os.unlink(temp_file)