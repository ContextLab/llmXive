"""
Unit tests for environment validation script.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Import the module to test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))
from env_validator import (
    check_python_version,
    check_cuda_availability,
    check_gpu_packages,
    check_memory_limit,
    check_dependencies,
    run_validation
)


class TestPythonVersion:
    def test_python_version_ok(self):
        """Test that current Python version passes."""
        passed, msg = check_python_version()
        assert passed is True
        assert "OK" in msg


class TestCudaAvailability:
    @patch('env_validator.os.environ.get', return_value='')
    @patch('env_validator.torch')
    def test_no_cuda_no_torch(self, mock_torch, mock_env):
        """Test when CUDA is not available and torch is not installed."""
        mock_torch.__version__ = '2.0.0'
        mock_torch.cuda.is_available.return_value = False

        passed, msg = check_cuda_availability()
        assert passed is False  # No CUDA available
        assert "OK" in msg

    @patch('env_validator.os.environ.get', return_value='0')
    @patch('env_validator.torch')
    def test_cuda_visible_devices_set(self, mock_torch, mock_env):
        """Test when CUDA_VISIBLE_DEVICES is set."""
        mock_torch.cuda.is_available.return_value = True

        has_cuda, msg = check_cuda_availability()
        assert has_cuda is True
        assert "WARNING" in msg


class TestGpuPackages:
    @patch('env_validator.subprocess.run')
    def test_no_gpu_packages(self, mock_run):
        """Test when no GPU packages are installed."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'pip')

        has_packages, packages = check_gpu_packages()
        assert has_packages is False
        assert len(packages) == 0

    @patch('env_validator.subprocess.run')
    def test_gpu_packages_detected(self, mock_run):
        """Test when GPU packages are installed."""
        mock_run.return_value = MagicMock(returncode=0)

        has_packages, packages = check_gpu_packages()
        assert has_packages is True
        assert len(packages) > 0


class TestMemoryLimit:
    def test_memory_limit_check(self):
        """Test memory limit check function."""
        passed, msg = check_memory_limit()
        # Should either pass or skip (if psutil not installed)
        assert isinstance(passed, bool)
        assert isinstance(msg, str)


class TestDependencies:
    @patch('env_validator.subprocess.run')
    def test_all_dependencies_installed(self, mock_run):
        """Test when all dependencies are installed."""
        mock_run.return_value = MagicMock(returncode=0)

        passed, missing = check_dependencies()
        assert passed is True
        assert len(missing) == 0

    @patch('env_validator.subprocess.run')
    def test_missing_dependencies(self, mock_run):
        """Test when some dependencies are missing."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'pip')

        passed, missing = check_dependencies()
        assert passed is False
        assert len(missing) > 0


class TestRunValidation:
    def test_run_validation_structure(self):
        """Test that run_validation returns expected structure."""
        results = run_validation()

        assert "timestamp" in results
        assert "validation_passed" in results
        assert "checks" in results
        assert isinstance(results["checks"], dict)

        # Check all expected keys are present
        expected_checks = [
            "python_version",
            "cuda_availability",
            "gpu_packages",
            "memory_limit",
            "dependencies"
        ]
        for check in expected_checks:
            assert check in results["checks"]
            assert "passed" in results["checks"][check]
            assert "message" in results["checks"][check]
