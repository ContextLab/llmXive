import subprocess
import os
import sys
import tempfile
import shutil
import pytest

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    assert os.path.exists(".flake8"), "Missing .flake8 configuration file"

def test_pyproject_toml_config_exists():
    """Verify pyproject.toml exists with tool configurations."""
    assert os.path.exists("pyproject.toml"), "Missing pyproject.toml configuration file"

def test_black_config_valid():
    """Verify black configuration is valid by running black --check on a dummy file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dummy_file = os.path.join(tmpdir, "dummy.py")
        with open(dummy_file, "w") as f:
            f.write("x=1\n")
        
        # Run black in check mode (should fail on unformatted file)
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", dummy_file],
            capture_output=True,
            text=True
        )
        # We expect it to fail because the file is unformatted, 
        # but the config should be valid
        assert "Invalid value" not in result.stderr, "Black configuration is invalid"

def test_flake8_config_valid():
    """Verify flake8 configuration is valid by running flake8 on a dummy file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dummy_file = os.path.join(tmpdir, "dummy.py")
        with open(dummy_file, "w") as f:
            f.write("x = 1\n")
        
        # Run flake8 on the dummy file
        result = subprocess.run(
            [sys.executable, "-m", "flake8", dummy_file],
            capture_output=True,
            text=True
        )
        # Should not raise configuration errors
        assert "configparser" not in result.stderr.lower(), "Flake8 configuration is invalid"
        assert "No such file" not in result.stderr, "Flake8 configuration is invalid"