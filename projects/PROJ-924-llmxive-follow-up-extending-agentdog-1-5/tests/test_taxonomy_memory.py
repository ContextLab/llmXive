"""
Tests for memory monitoring in taxonomy_builder.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "projects" / "PROJ-924-llmxive-follow-up-extending-agentdog-1-5" / "code"))

from taxonomy_builder import MemoryLimitExceededError

def test_memory_limit_exception():
    """Test that MemoryLimitExceededError is properly defined and raised."""
    try:
        raise MemoryLimitExceededError("Test memory limit exceeded")
    except MemoryLimitExceededError as e:
        assert str(e) == "Test memory limit exceeded"
    except Exception:
        pytest.fail("MemoryLimitExceededError was not raised correctly")

def test_memory_limit_exception_message():
    """Test that MemoryLimitExceededError has the correct message."""
    error = MemoryLimitExceededError("Peak memory usage exceeded")
    assert "Peak memory usage exceeded" in str(error)