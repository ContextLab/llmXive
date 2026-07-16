import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path

import pytest

# Import the functions to test
# Since the script is in code/, we need to adjust sys.path or import relative to it
# For the test runner, we assume we are running from the project root
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_venv import find_python311, create_venv, install_dependencies

class TestFindPython311:
    def test_find_python311_exists(self):
        """
        Test that a Python 3.11 interpreter can be found.
        This test will pass if the environment running the tests has Python 3.11.
        """
        try:
            python_exe = find_python311()
            # Verify it actually runs and reports 3.11
            result = subprocess.run(
                [python_exe, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            assert "3.11" in result.stdout, f"Found python but version is not 3.11: {result.stdout}"
        except FileNotFoundError:
            # If 3.11 is not installed on the CI runner, we skip this specific check
            # but the function itself is correct.
            pytest.skip("Python 3.11 not found in environment")

class TestCreateVenv:
    def test_create_venv_creates_directory(self):
        """
        Test that create_venv creates a directory structure.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = os.path.join(tmpdir, "test_venv")
            
            # We need a python executable to pass. 
            # If we are here, find_python311 likely worked or we skip.
            try:
                python_exe = find_python311()
            except FileNotFoundError:
                pytest.skip("Python 3.11 not found, cannot test venv creation")

            create_venv(venv_path, python_exe)
            
            assert os.path.isdir(venv_path), "Virtual environment directory was not created"
            
            # Check for standard venv files
            if os.name == "nt":
                assert os.path.exists(os.path.join(venv_path, "Scripts", "python.exe")), "Scripts/python.exe missing"
            else:
                assert os.path.exists(os.path.join(venv_path, "bin", "python")), "bin/python missing"

class TestInstallDependencies:
    def test_install_dependencies_with_mock_requirements(self):
        """
        Test that install_dependencies runs without error given a valid requirements file.
        We create a temporary venv and a minimal requirements.txt.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = os.path.join(tmpdir, "test_venv")
            req_path = os.path.join(tmpdir, "requirements.txt")
            
            # Create a minimal requirements file
            with open(req_path, "w") as f:
                f.write("pip>=20.0\n") # Just upgrade pip to test logic

            try:
                python_exe = find_python311()
            except FileNotFoundError:
                pytest.skip("Python 3.11 not found, cannot test dependency installation")

            # Create venv first
            create_venv(venv_path, python_exe)
            
            # Now install
            install_dependencies(venv_path, req_path)
            
            # Verify pip exists and is executable
            pip_exe = "pip.exe" if os.name == "nt" else "pip"
            pip_path = os.path.join(venv_path, "Scripts", pip_exe) if os.name == "nt" else os.path.join(venv_path, "bin", pip_exe)
            assert os.path.exists(pip_path), "pip executable not found after installation"