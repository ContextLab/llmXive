"""
Tests for the pytest configuration itself (T004).

Verifies that CPU resource limit markers are registered and that the
resource-limit fixtures behave correctly.
"""

import pytest


CPU_MARKERS = ("cpu_limit", "memory_limit", "resource_limits")


def test_cpu_limit_markers_registered():
    """All CPU resource limit markers must be registered with pytest."""
    for marker in CPU_MARKERS:
        assert pytest.mark.__getattr__(marker) is not None


@pytest.mark.cpu_limit
def test_cpu_limit_fixture(cpu_limit_env):
    """The cpu_limit_env fixture enforces CPU-only, <=2 vCPU execution."""
    assert cpu_limit_env["device"] == "cpu"
    assert cpu_limit_env["max_vcpus"] == 2
    assert cpu_limit_env["torch_threads"] <= 2


@pytest.mark.memory_limit
def test_memory_limit_guard_fixture(memory_limit_guard):
    """The memory_limit_guard fixture checks RSS stays under 7GB."""
    rss_gb = memory_limit_guard()
    assert 0.0 <= rss_gb < 7.0


@pytest.mark.resource_limits
@pytest.mark.cpu_limit
@pytest.mark.memory_limit
def test_combined_resource_limits(cpu_limit_env, memory_limit_guard):
    """Markers and fixtures compose for full edge-environment checks."""
    assert cpu_limit_env["max_vcpus"] == 2
    memory_limit_guard()


def test_source_packages_importable():
    """code/src must be importable as `src` for the rest of the suite."""
    import src  # noqa: F401
    import src.utils  # noqa: F401