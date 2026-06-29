"""
Unit tests for install_dependencies.py (Task T002b)

These tests verify the install_dependencies script logic without
actually running pip install.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch, MagicMock

# Add code/setup to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code" / "setup"))

from install_dependencies import (
    get_venv_paths,
    create_virtual_environment,
    install_dependencies,
    verify_installation,
)


class TestGetVenvPaths(TestCase):
    """Tests for get_venv_paths function."""

    def test_unix_paths(self):
        """Test that Unix paths are returned correctly."""
        with patch("os.name", "posix"):
            venv_path = Path("/test/venv")
            activate_script, pip_path = get_venv_paths(venv_path)
            
            self.assertEqual(str(activate_script), "/test/venv/bin/activate")
            self.assertEqual(str(pip_path), "/test/venv/bin/pip")

    def test_windows_paths(self):
        """Test that Windows paths are returned correctly."""
        with patch("os.name", "nt"):
            venv_path = Path("C:\\test\\venv")
            activate_script, pip_path = get_venv_paths(venv_path)
            
            self.assertEqual(str(activate_script), "C:\\test\\venv\\Scripts\\activate.bat")
            self.assertEqual(str(pip_path), "C:\\test\\venv\\Scripts\\pip.exe")


class TestCreateVirtualEnvironment(TestCase):
    """Tests for create_virtual_environment function."""

    def test_existing_venv_returns_true(self):
        """Test that existing venv returns True without recreating."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "venv"
            venv_path.mkdir(parents=True)
            
            # Create a marker file to simulate existing venv
            (venv_path / "pyvenv.cfg").touch()
            
            with patch("subprocess.run") as mock_run:
                result = create_virtual_environment(venv_path)
                
                self.assertTrue(result)
                mock_run.assert_not_called()  # Should not create new venv

    def test_new_venv_creates_directory(self):
        """Test that new venv is created successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "venv"
            
            # Mock successful venv creation
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            
            with patch("subprocess.run", return_value=mock_result) as mock_run:
                result = create_virtual_environment(venv_path)
                
                self.assertTrue(result)
                mock_run.assert_called_once()

    def test_failed_venv_returns_false(self):
        """Test that failed venv creation returns False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "venv"
            
            # Mock failed venv creation
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "Error: venv creation failed"
            
            with patch("subprocess.run", return_value=mock_result):
                result = create_virtual_environment(venv_path)
                
                self.assertFalse(result)


class TestInstallDependencies(TestCase):
    """Tests for install_dependencies function."""

    def test_missing_requirements_file_returns_false(self):
        """Test that missing requirements file returns False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "venv"
            requirements_file = Path(tmpdir) / "nonexistent.txt"
            
            result = install_dependencies(venv_path, requirements_file)
            
            self.assertFalse(result)

    def test_successful_install_returns_true(self):
        """Test that successful installation returns True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "venv"
            requirements_file = Path(tmpdir) / "requirements.txt"
            
            # Create requirements file
            requirements_file.write_text("pandas>=2.0.0\n")
            
            # Create fake pip path
            if os.name == "nt":
                pip_path = venv_path / "Scripts" / "pip.exe"
            else:
                pip_path = venv_path / "bin" / "pip"
            pip_path.parent.mkdir(parents=True, exist_ok=True)
            pip_path.touch()
            
            # Mock successful pip install
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_result.stdout = "Successfully installed pandas"
            
            with patch("subprocess.run", return_value=mock_result):
                result = install_dependencies(venv_path, requirements_file)
                
                self.assertTrue(result)

    def test_failed_install_returns_false(self):
        """Test that failed installation returns False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "venv"
            requirements_file = Path(tmpdir) / "requirements.txt"
            
            # Create requirements file
            requirements_file.write_text("invalid-package-xyz>=1.0.0\n")
            
            # Create fake pip path
            if os.name == "nt":
                pip_path = venv_path / "Scripts" / "pip.exe"
            else:
                pip_path = venv_path / "bin" / "pip"
            pip_path.parent.mkdir(parents=True, exist_ok=True)
            pip_path.touch()
            
            # Mock failed pip install
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "ERROR: Could not find a version that satisfies the requirement"
            mock_result.stdout = ""
            
            with patch("subprocess.run", return_value=mock_result):
                result = install_dependencies(venv_path, requirements_file)
                
                self.assertFalse(result)


class TestVerifyInstallation(TestCase):
    """Tests for verify_installation function."""

    def test_missing_pip_returns_false(self):
        """Test that missing pip returns False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "venv"
            
            result = verify_installation(venv_path)
            
            self.assertFalse(result)

    def test_all_packages_installed_returns_true(self):
        """Test that all required packages verified returns True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "venv"
            
            # Create fake pip path
            if os.name == "nt":
                pip_path = venv_path / "Scripts" / "pip.exe"
            else:
                pip_path = venv_path / "bin" / "pip"
            pip_path.parent.mkdir(parents=True, exist_ok=True)
            pip_path.touch()
            
            # Mock pip list showing all required packages
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = """
            Package         Version
            --------------- -------
            pandas          2.0.0
            numpy           1.24.0
            scipy           1.11.0
            scikit-learn    1.3.0
            matplotlib      3.7.0
            pyyaml          6.0
            requests        2.28.0
            """
            mock_result.stderr = ""
            
            with patch("subprocess.run", return_value=mock_result):
                result = verify_installation(venv_path)
                
                self.assertTrue(result)

    def test_missing_packages_returns_false(self):
        """Test that missing packages returns False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "venv"
            
            # Create fake pip path
            if os.name == "nt":
                pip_path = venv_path / "Scripts" / "pip.exe"
            else:
                pip_path = venv_path / "bin" / "pip"
            pip_path.parent.mkdir(parents=True, exist_ok=True)
            pip_path.touch()
            
            # Mock pip list showing missing packages
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = """
            Package    Version
            ---------- -------
            pandas     2.0.0
            numpy      1.24.0
            """
            mock_result.stderr = ""
            
            with patch("subprocess.run", return_value=mock_result):
                result = verify_installation(venv_path)
                
                self.assertFalse(result)


if __name__ == "__main__":
    main()