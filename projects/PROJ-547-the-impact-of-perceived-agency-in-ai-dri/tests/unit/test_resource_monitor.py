"""
Unit tests for the resource monitoring utilities.
"""
from unittest.mock import patch

import pytest

from utils.error_handler import PipelineError
from utils.resource_monitor import enforce_limits


def test_enforce_limits_within_bounds():
    """Test that enforce_limits passes when usage is within bounds."""
    with patch("utils.resource_monitor._get_current_ram_gb", return_value=1.0):
        with patch("utils.resource_monitor._get_current_cpu_cores", return_value=1.0):
            # Should not raise
            enforce_limits(max_ram_gb=2.0, max_cpu_cores=2.0)


def test_enforce_limits_exceeds_ram():
    """Test that enforce_limits raises PipelineError when RAM is exceeded."""
    with patch("utils.resource_monitor._get_current_ram_gb", return_value=10.0):
        with patch("utils.resource_monitor._get_current_cpu_cores", return_value=1.0):
            with pytest.raises(PipelineError) as exc_info:
                enforce_limits(max_ram_gb=2.0, max_cpu_cores=2.0)
            assert "RAM usage" in str(exc_info.value.message)
            assert exc_info.value.code == 1001


def test_enforce_limits_exceeds_cpu():
    """Test that enforce_limits raises PipelineError when CPU is exceeded."""
    with patch("utils.resource_monitor._get_current_ram_gb", return_value=1.0):
        with patch("utils.resource_monitor._get_current_cpu_cores", return_value=5.0):
            with pytest.raises(PipelineError) as exc_info:
                enforce_limits(max_ram_gb=2.0, max_cpu_cores=2.0)
            assert "CPU usage" in str(exc_info.value.message)
            assert exc_info.value.code == 1002
