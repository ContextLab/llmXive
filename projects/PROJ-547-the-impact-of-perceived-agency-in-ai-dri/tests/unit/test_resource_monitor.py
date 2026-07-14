"""
Unit tests for the resource_monitor module.
"""

import pytest

from utils.error_handler import PipelineError
from utils.resource_monitor import enforce_limits


def test_enforce_limits_success():
    """Test that enforce_limits passes when under limits."""
    # Set high limits to ensure we pass
    try:
        enforce_limits(max_ram_gb=100.0, max_cpu_cores=100.0)
    except PipelineError:
        pytest.fail("enforce_limits raised PipelineError unexpectedly")


def test_enforce_limits_ram_exceeded():
    """Test that enforce_limits fails when RAM limit is exceeded."""
    # Set a very low RAM limit to force failure
    with pytest.raises(PipelineError) as exc_info:
        enforce_limits(max_ram_gb=0.0001)  # 0.1 MB limit
    assert "RAM limit exceeded" in str(exc_info.value)