import os
from unittest import mock

import pytest

from utils.resource_monitor import enforce_limits
from utils.error_handler import PipelineError


def test_memory_limit_exceeded(monkeypatch):
    """Simulate memory usage above the 6 GB threshold."""
    # 7 GB in bytes
    mock_memory = 7 * 1024 ** 3

    mock_process = mock.Mock()
    mock_process.memory_info.return_value = mock.Mock(rss=mock_memory)
    monkeypatch.setattr("psutil.Process", lambda: mock_process)

    # Normal CPU count
    monkeypatch.setattr(os, "cpu_count", lambda: 1)

    with pytest.raises(PipelineError) as exc:
        enforce_limits()
    assert "Memory usage" in str(exc.value)


def test_cpu_limit_exceeded(monkeypatch):
    """Simulate a machine with more than 2 CPU cores."""
    # Normal memory usage (1 GB)
    mock_memory = 1 * 1024 ** 3
    mock_process = mock.Mock()
    mock_process.memory_info.return_value = mock.Mock(rss=mock_memory)
    monkeypatch.setattr("psutil.Process", lambda: mock_process)

    # Simulate 4 CPU cores
    monkeypatch.setattr(os, "cpu_count", lambda: 4)

    with pytest.raises(PipelineError) as exc:
        enforce_limits()
    assert "CPU core count" in str(exc.value)


def test_within_limits(monkeypatch):
    """When both memory and CPU are within limits, no exception is raised."""
    mock_memory = 1 * 1024 ** 3
    mock_process = mock.Mock()
    mock_process.memory_info.return_value = mock.Mock(rss=mock_memory)
    monkeypatch.setattr("psutil.Process", lambda: mock_process)

    monkeypatch.setattr(os, "cpu_count", lambda: 1)

    # Should complete without raising
    enforce_limits()
