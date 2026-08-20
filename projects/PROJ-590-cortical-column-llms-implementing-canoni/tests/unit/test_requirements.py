"""
Unit tests for environment setup and requirements verification.
"""
import pytest
import sys
import importlib

from setup_environment import check_import, _version_gte, REQUIRED_PACKAGES


class TestVersionComparison:
    """Tests for version comparison logic."""

    def test_version_gte_equal(self):
        """Test that equal versions return True."""
        assert _version_gte("2.1.0", "2.1.0") is True

    def test_version_gte_greater(self):
        """Test that greater version returns True."""
        assert _version_gte("2.2.0", "2.1.0") is True
        assert _version_gte("3.0.0", "2.1.0") is True

    def test_version_gte_less(self):
        """Test that lesser version returns False."""
        assert _version_gte("2.0.0", "2.1.0") is False
        assert _version_gte("1.9.0", "2.1.0") is False

    def test_version_gte_patch_level(self):
        """Test patch level comparisons."""
        assert _version_gte("2.1.1", "2.1.0") is True
        assert _version_gte("2.1.0", "2.1.1") is False


class TestRequiredPackages:
    """Tests for required package definitions."""

    def test_required_packages_defined(self):
        """Test that REQUIRED_PACKAGES is a non-empty dictionary."""
        assert isinstance(REQUIRED_PACKAGES, dict)
        assert len(REQUIRED_PACKAGES) > 0

    def test_all_required_packages_have_versions(self):
        """Test that all required packages have version specifications."""
        for package, version in REQUIRED_PACKAGES.items():
            assert isinstance(package, str)
            assert isinstance(version, str)
            assert len(version) > 0

    def test_torch_cpu_only(self):
        """Test that torch is in required packages."""
        assert 'torch' in REQUIRED_PACKAGES

    def test_numpy_required(self):
        """Test that numpy is in required packages."""
        assert 'numpy' in REQUIRED_PACKAGES

    def test_scipy_required(self):
        """Test that scipy is in required packages."""
        assert 'scipy' in REQUIRED_PACKAGES

    def test_pytest_required(self):
        """Test that pytest is in required packages."""
        assert 'pytest' in REQUIRED_PACKAGES

    def test_psutil_required(self):
        """Test that psutil is in required packages."""
        assert 'psutil' in REQUIRED_PACKAGES


class TestCheckImport:
    """Tests for the check_import function."""

    def test_check_import_existing_package(self):
        """Test checking an existing package."""
        # sys is always available
        result = check_import('sys')
        assert result is True

    def test_check_import_nonexistent_package(self):
        """Test checking a non-existent package."""
        result = check_import('nonexistent_package_xyz_123')
        assert result is False

    def test_check_import_with_version(self):
        """Test checking package with version requirement."""
        # Check sys (no version attribute) - should return True
        result = check_import('sys', '1.0.0')
        assert result is True

    def test_check_import_pytest(self):
        """Test checking pytest package."""
        result = check_import('pytest')
        assert result is True

    def test_check_import_numpy(self):
        """Test checking numpy package."""
        result = check_import('numpy')
        assert result is True


class TestEnvironmentSetup:
    """Tests for environment setup module."""

    def test_import_module(self):
        """Test that setup_environment module can be imported."""
        import setup_environment
        assert hasattr(setup_environment, 'check_import')
        assert hasattr(setup_environment, 'main')
        assert hasattr(setup_environment, 'REQUIRED_PACKAGES')

    def test_main_function_exists(self):
        """Test that main function exists and is callable."""
        from setup_environment import main
        assert callable(main)