"""
Unit tests for code/utils/resource_guard.py
"""
import pytest
from code.utils.resource_guard import ResourceLimitExceededError, GPUForbiddenError, check_cpu_only


class TestResourceLimitExceededError:
    def test_error_creation(self):
        error = ResourceLimitExceededError("RAM limit exceeded")
        assert str(error) == "RAM limit exceeded"
        assert isinstance(error, Exception)

    def test_error_with_details(self):
        error = ResourceLimitExceededError("Memory limit", used=8, limit=7)
        assert "Memory limit" in str(error)


class TestGPUForbiddenError:
    def test_error_creation(self):
        error = GPUForbiddenError("GPU usage not allowed")
        assert str(error) == "GPU usage not allowed"
        assert isinstance(error, Exception)


class TestCheckCpuOnly:
    def test_check_cpu_only_no_gpu(self):
        # This test assumes no GPU is available in the test environment
        # In a real GPU environment, this would raise GPUForbiddenError
        try:
            check_cpu_only()
        except GPUForbiddenError:
            pytest.fail("check_cpu_only should not raise when no GPU is present")

    def test_check_cpu_only_function_exists(self):
        # Verify the function exists and is callable
        assert callable(check_cpu_only)
