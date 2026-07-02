import sys
import importlib.util
import pytest
from unittest.mock import patch
from code.setup_environment import check_python_version, check_packages, REQUIRED_PACKAGES

def test_check_python_version_success():
    """Test that current Python version passes check."""
    # Since we are running in the target env, this should pass
    assert check_python_version() is True

def test_check_python_version_failure():
    """Test that a lower version fails check."""
    with patch('code.setup_environment.sys.version_info') as mock_version:
        mock_version.major = 3
        mock_version.minor = 8
        mock_version.micro = 0
        assert check_python_version((3, 11, 0)) is False

def test_check_packages_installed():
    """Test that required packages are detected as installed."""
    # Check against the actual environment
    assert check_packages(REQUIRED_PACKAGES) is True

def test_check_packages_missing():
    """Test detection of missing packages."""
    with patch('importlib.util.find_spec') as mock_find:
        # Make all packages look missing
        mock_find.return_value = None
        assert check_packages(["pandas"]) is False
        mock_find.assert_called()
