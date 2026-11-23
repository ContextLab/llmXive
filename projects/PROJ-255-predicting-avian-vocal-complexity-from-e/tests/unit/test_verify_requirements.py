"""
Unit tests for T002b requirements verification logic.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from verify_requirements import (
    EXPECTED_PACKAGES,
    get_project_root,
    verify_requirements_file,
    install_requirements
)


class TestVerifyRequirements:
    """Test suite for requirements verification."""

    def test_expected_packages_defined(self):
        """Test that EXPECTED_PACKAGES is properly defined."""
        assert len(EXPECTED_PACKAGES) == 12
        assert "librosa==0.10.1" in EXPECTED_PACKAGES
        assert "statsmodels==0.14.0" in EXPECTED_PACKAGES
        assert "osmnx==1.8.0" in EXPECTED_PACKAGES
        assert "geopy==2.4.0" in EXPECTED_PACKAGES

    def test_get_project_root(self):
        """Test that get_project_root returns a Path object."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()

    @patch('builtins.open')
    @patch('pathlib.Path.exists')
    def test_verify_requirements_file_not_found(self, mock_exists, mock_open):
        """Test verification when requirements.txt is not found."""
        mock_exists.return_value = False
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = verify_requirements_file(root)
            assert result is False

    @patch('builtins.open')
    @patch('pathlib.Path.exists')
    def test_verify_requirements_file_wrong_content(self, mock_exists, mock_open):
        """Test verification when requirements.txt has wrong content."""
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = "wrong-package==1.0.0\n"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = verify_requirements_file(root)
            assert result is False

    @patch('builtins.open')
    @patch('pathlib.Path.exists')
    def test_verify_requirements_file_correct(self, mock_exists, mock_open):
        """Test verification when requirements.txt has correct content."""
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = "\n".join(EXPECTED_PACKAGES)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            result = verify_requirements_file(root)
            assert result is True

    @patch('subprocess.run')
    def test_install_requirements_success(self, mock_run):
        """Test successful installation."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            # Create a dummy requirements.txt
            req_file = root / "requirements.txt"
            req_file.write_text("\n".join(EXPECTED_PACKAGES))
            
            result = install_requirements(root)
            assert result is True
            mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_install_requirements_failure(self, mock_run):
        """Test failed installation."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="Error output",
            stderr="Pip error"
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            req_file = root / "requirements.txt"
            req_file.write_text("\n".join(EXPECTED_PACKAGES))
            
            result = install_requirements(root)
            assert result is False

    def test_package_list_completeness(self):
        """Test that all required packages are in the list."""
        required_packages = [
            "librosa", "statsmodels", "osmnx", "geopy", "pandas",
            "scikit-learn", "matplotlib", "seaborn", "requests",
            "datasets", "pytest", "pyyaml"
        ]
        
        for pkg in required_packages:
            found = any(pkg in p for p in EXPECTED_PACKAGES)
            assert found, f"Package {pkg} not found in EXPECTED_PACKAGES"