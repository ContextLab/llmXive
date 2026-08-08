"""
Unit tests for the environment initialization module.
"""
import sys
import importlib.util
from unittest.mock import patch, MagicMock
import pytest

from code.init_env import check_package, REQUIRED_PACKAGES, main

def test_check_package_existing():
    """Test that check_package returns True for an existing package."""
    # sys should always be available
    assert check_package("sys") is True

def test_check_package_non_existing():
    """Test that check_package returns False for a non-existing package."""
    # Use a clearly fake package name
    assert check_package("this_package_definitely_does_not_exist_xyz") is False

def test_required_packages_list_not_empty():
    """Ensure the REQUIRED_PACKAGES list has content."""
    assert len(REQUIRED_PACKAGES) > 0
    assert "pandas" in REQUIRED_PACKAGES
    assert "numpy" in REQUIRED_PACKAGES

def test_main_success():
    """Test main() when all packages are present (mocked)."""
    with patch('code.init_env.check_package', return_value=True):
        with patch('sys.exit') as mock_exit:
            with patch('builtins.print'):  # Suppress prints
                main()
            mock_exit.assert_called_once_with(0)

def test_main_failure():
    """Test main() when some packages are missing (mocked)."""
    def mock_check(pkg):
        return pkg != "missing_pkg"
    
    with patch('code.init_env.check_package', side_effect=mock_check):
        with patch('sys.exit') as mock_exit:
            with patch('builtins.print'):
                main()
            mock_exit.assert_called_once_with(1)