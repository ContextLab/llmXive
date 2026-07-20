"""
Unit tests for dependency setup functionality.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys

# Import the module to test
# Adjust import path based on project structure
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from code.setup_dependencies import check_installation, install_dependencies

class TestCheckInstallation:
    """Tests for check_installation function."""
    
    def test_check_installed_package(self):
        """Test checking for a package that should be installed."""
        # os is always available
        assert check_installation("os") is True

    def test_check_uninstalled_package(self):
        """Test checking for a package that likely isn't installed."""
        # Using a package name that is unlikely to exist in the base env
        # Note: This test might be flaky if the package happens to be installed
        # A better approach is to mock the import
        with patch('builtins.__import__', side_effect=ImportError("No module")):
            assert check_installation("nonexistent_package_xyz") is False

class TestInstallDependencies:
    """Tests for install_dependencies function."""
    
    def test_install_from_valid_file(self, tmp_path):
        """Test installation from a valid requirements file."""
        req_file = tmp_path / "requirements.txt"
        req_file.write_text("os\n") # 'os' is a stdlib module, pip will ignore or handle gracefully
        
        # Mock subprocess.run to avoid actual installation during tests
        with patch('code.setup_dependencies.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock()
            install_dependencies(req_file)
            mock_run.assert_called_once()
            
    def test_install_from_missing_file(self, tmp_path):
        """Test installation from a missing requirements file."""
        missing_file = tmp_path / "missing.txt"
        
        with pytest.raises(SystemExit):
            install_dependencies(missing_file)