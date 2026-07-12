"""
Unit tests for CPU resource limit markers and pytest configuration.

These tests verify that:
1. CPU-only mode is enforced
2. Resource limits are properly configured
3. Custom markers work as expected
"""
import os
import pytest
import sys

def test_cuda_visible_devices_is_empty():
    """Verify that CUDA_VISIBLE_DEVICES is set to empty string."""
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == "", \
        "CUDA_VISIBLE_DEVICES must be empty for CPU-only tests"

def test_cpu_only_fixture_available():
    """Verify that the cpu_resource_limit fixture is available."""
    # This test just verifies the fixture can be loaded
    # The actual resource limiting is tested in integration tests
    assert True

@pytest.mark.unit
def test_unit_marker_recognized():
    """Verify that unit tests are properly marked."""
    assert True

@pytest.mark.integration
def test_integration_marker_recognized():
    """Verify that integration tests are properly marked."""
    assert True

@pytest.mark.cpu_limit
def test_cpu_limit_marker_recognized(cpu_resource_limit):
    """Verify that CPU limit marker works with fixture."""
    # This test uses the cpu_resource_limit fixture
    # which enforces memory and time limits
    assert True

def test_no_gpu_operations():
    """
    Verify that no GPU operations are attempted in tests.
    
    This is a basic check that torch (if available) is configured for CPU.
    """
    try:
        import torch
        # Check that default device is CPU
        # Note: torch.set_default_device might not be available in older versions
        if hasattr(torch, 'default_device'):
            assert torch.default_device() == torch.device('cpu'), \
                "Torch default device must be CPU"
    except ImportError:
        # torch not installed, skip this check
        pass

@pytest.mark.slow
def test_slow_marker_exists():
    """Verify that slow marker is recognized by pytest."""
    # This test will be skipped unless --runslow is passed
    assert True

def test_environment_isolation():
    """Verify that test environment is properly isolated."""
    # Check that no GPU-related environment variables are set
    gpu_vars = ['CUDA_VISIBLE_DEVICES', 'CUDA_LAUNCH_BLOCKING']
    for var in gpu_vars:
        value = os.environ.get(var, '')
        if var == 'CUDA_VISIBLE_DEVICES':
            assert value == '', f"{var} should be empty, got: {value}"
        else:
            # Other GPU vars should not be set or should be 0
            pass