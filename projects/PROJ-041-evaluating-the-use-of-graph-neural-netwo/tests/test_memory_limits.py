import pytest
from utils.memory_monitor import MemoryLimitError, run_with_limit

def _dummy_allocation():
    # Allocate ~100MB to ensure it's not 0, but small enough for the test.
    return bytearray(100 * 1024 * 1024)

def test_memory_limit_error():
    """Verify that run_with_limit raises MemoryLimitError when limit is exceeded."""
    with pytest.raises(MemoryLimitError):
        # Set limit to 0.001 GB (~1MB), allocation is 100MB.
        run_with_limit(0.001, _dummy_allocation)
