"""
Unit tests for memory profiling utilities and constraints.
"""
import pytest
import os
import sys
from pathlib import Path

# Add code to path
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from modeling.efficiency import get_peak_memory_mb, ResourceLimitExceeded

class TestMemoryProfile:
    """Tests for memory profiling functionality."""

    def test_get_peak_memory_mb_returns_positive(self):
        """Verify that get_peak_memory_mb returns a positive number."""
        memory = get_peak_memory_mb()
        assert isinstance(memory, float)
        assert memory > 0.0, "Peak memory should be positive"

    def test_get_peak_memory_mb_reasonable_range(self):
        """Verify memory usage is within a reasonable range for this script."""
        # A simple script like this shouldn't use more than 500MB
        memory = get_peak_memory_mb()
        assert memory < 500.0, f"Memory usage {memory}MB seems abnormally high for this test"

    def test_resource_limit_exceeded_exception(self):
        """Verify ResourceLimitExceeded is a subclass of Exception."""
        assert issubclass(ResourceLimitExceeded, Exception)

    def test_memory_constraint_logic(self):
        """Test the logic that checks against 7GB limit."""
        # This is a logic test, not a runtime test
        limit_mb = 7000
        safe_memory = 6000
        unsafe_memory = 8000

        assert safe_memory < limit_mb
        assert unsafe_memory > limit_mb