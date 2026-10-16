"""
Unit tests for ``code.utils.memory_monitor``.

The tests ensure that the hard memory limit enforcement works as
specified in the task description.
"""

import pytest

from utils.memory_monitor import (
    MemoryLimitExceededError,
    run_with_limit,
    memory_limit,
)


def test_run_with_limit_raises_when_exceeding():
    """
    ``run_with_limit`` should raise ``MemoryLimitExceededError`` when the
    requested dummy allocation exceeds the configured hard limit.
    """
    # The default limit is 7 GB (7168 MB). Requesting 8 GB must raise.
    with pytest.raises(MemoryLimitExceededError):
        run_with_limit(limit_gb=8.0)


def test_run_with_limit_passes_when_within_limit():
    """
    When the dummy allocation is within the limit, ``run_with_limit`` must
    return ``None`` without raising.
    """
    # Request a value comfortably below the limit.
    result = run_with_limit(limit_gb=1.0)
    assert result is None


def test_memory_limit_is_configurable_via_env(monkeypatch):
    """
    The global ``memory_limit`` can be overridden by the ``MEMORY_LIMIT_MB``
    environment variable. This test patches the environment to a small
    value and verifies that ``run_with_limit`` respects it.
    """
    # Set a tiny limit (e.g., 10 MB)
    monkeypatch.setenv("MEMORY_LIMIT_MB", "10")
    # Reload the module to pick up the new env var
    import importlib

    import utils.memory_monitor as mm

    importlib.reload(mm)

    # The limit is now 10 MB → 0.0098 GB, so a 0.02 GB request should fail
    with pytest.raises(mm.MemoryLimitExceededError):
        mm.run_with_limit(limit_gb=0.02)


def test_jsonschema_validation_simple():
    """
    A minimal sanity‑check that the ``jsonschema`` library works.
    """
    import jsonschema

    schema = {"type": "object", "properties": {"a": {"type": "integer"}}}
    instance = {"a": 1}
    # Should not raise
    jsonschema.validate(instance=instance, schema=schema)
