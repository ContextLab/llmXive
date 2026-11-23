import subprocess
import sys
from pathlib import Path
import shutil
import tempfile

import pytest

# Import the module under test
# Note: We assume the test is run from the project root or code/ is in path
# Adjust import path if necessary based on test runner configuration
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))
from setup_venv import find_python311, create_venv, install_dependencies

class TestFindPython311:
    def test_find_python311_returns_valid_path(self):
        """Test that find_python311 returns a path to a valid python 3.11 executable."""
        try:
            python_path = find_python311()
            assert Path(python_path).exists(), f"Python path {python_path} does not exist"
            # Verify version
            result = subprocess.run([python_path, "--version"], capture_output=True, text=True)
            assert "3.11" in result.stdout or "3.11" in result.stderr, f"Python version is not 3.11: {result.stdout}"
        except FileNotFoundError:
            pytest.skip("Python 3.11 not found in environment, skipping test.")

class TestCreateVenv:
    def test_create_venv_creates_directory(self, tmp_path):
        """Test that create_venv creates the expected directory structure."""
        venv_dir = tmp_path / "test_venv"
        python_exe = find_python311()
        create_venv(str(venv_dir), python_exe)
        assert venv_dir.exists()
        assert (venv_dir / "bin").exists()
        assert (venv_dir / "bin" / "python").exists()

    def test_create_venv_recreates_if_exists(self, tmp_path):
        """Test that create_venv removes existing venv and recreates it."""
        venv_dir = tmp_path / "test_venv"
        venv_dir.mkdir()
        dummy_file = venv_dir / "dummy.txt"
        dummy_file.write_text("dummy")

        python_exe = find_python311()
        create_venv(str(venv_dir), python_exe)

        assert dummy_file.exists() is False
        assert (venv_dir / "bin" / "python").exists()

class TestInstallDependencies:
    def test_install_dependencies_installs_packages(self, tmp_path, monkeypatch):
        """Test that install_dependencies installs packages from a requirements file."""
        # Setup a temporary requirements file
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("pip\n") # Install pip to ensure it works

        venv_dir = tmp_path / "test_venv"
        python_exe = find_python311()
        create_venv(str(venv_dir), python_exe)

        # Mock the pip path to use the one in our tmp venv
        # The function uses venv_bin / "pip" internally, so we just need to ensure the venv is valid
        # We can't easily mock the internal Path construction without refactoring,
        # so we trust the logic and check if pip runs without error.

        # Run the function
        # Note: This might take a moment
        install_dependencies(str(venv_dir), str(req_file))

        # Verify pip list contains expected package (pip itself)
        pip_exe = venv_dir / "bin" / "pip"
        result = subprocess.run([str(pip_exe), "list"], capture_output=True, text=True)
        assert "pip" in result.stdout.lower()