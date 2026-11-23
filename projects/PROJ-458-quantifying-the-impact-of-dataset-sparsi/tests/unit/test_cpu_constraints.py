"""Unit tests for the CPU and memory constraint utilities."""

import pytest

from utils.cpu_constraints import enforce_memory_limit, chunked_iterator

def test_enforce_memory_limit_high_threshold():
    """A very high limit should never trigger a failure."""
    # 100 GB is far above any realistic usage in the test environment.
    assert enforce_memory_limit(100.0) is True

def test_chunked_iterator_basic():
    """Chunked iterator should split a list into expected chunk sizes."""
    data = list(range(10))  # Simple deterministic list
    chunks = list(chunked_iterator(data, chunk_size=3, memory_limit_gb=4.0))
    # Expected chunks: [0,1,2], [3,4,5], [6,7,8], [9]
    assert chunks == [ [0,1,2], [3,4,5], [6,7,8], [9] ]

def test_chunked_iterator_memory_limit():
    """
    With a tiny memory limit the iterator should stop early.
    We cannot reliably force OOM, but we can set a limit that will be
    exceeded after the first chunk (since the internal check uses the
    current process memory, which will be > 0.001 GB on any runner).
    """
    data = list(range(1000))
    # Set an unrealistically low limit to provoke early termination.
    chunks = list(chunked_iterator(data, chunk_size=200, memory_limit_gb=0.001))
    # At most one chunk should be produced because the memory check will fail
    # after the first successful chunk.
    assert len(chunks) <= 1

# The following ensures the module imports correctly without side effects.
def test_imports_without_error():
    """Simply importing the utilities should not raise."""
    try:
        from utils import cpu_constraints  # noqa: F401
    except Exception as exc:
        pytest.fail(f"Importing utils.cpu_constraints raised {exc}")