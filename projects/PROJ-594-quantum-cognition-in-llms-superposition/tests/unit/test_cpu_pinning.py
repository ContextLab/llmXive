"""
Unit tests for CPU Pinning Utility (T009c)
"""

import os
import pytest
import sys

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from utils.cpu_pinning import pin_to_core, get_available_cores, verify_pinning


class TestCpuPinning:
    """Tests for the cpu_pinning module."""

    def test_get_available_cores_returns_set(self):
        """Test that get_available_cores returns a non-empty set of integers."""
        cores = get_available_cores()
        assert isinstance(cores, set)
        assert len(cores) > 0
        assert all(isinstance(c, int) for c in cores)

    def test_pin_to_core_valid_core(self):
        """Test pinning to a valid available core."""
        available_cores = get_available_cores()
        # Pick the first available core
        target_core = next(iter(available_cores))

        # Pin to the core
        pin_to_core(target_core)

        # Verify the pinning
        assert verify_pinning(target_core), f"Process was not pinned to core {target_core}"

    def test_pin_to_core_invalid_core_raises_error(self):
        """Test that pinning to an unavailable core raises ValueError."""
        available_cores = get_available_cores()
        # Find a core that is definitely not available (e.g., max + 100)
        # Assuming available_cores is not empty
        max_core = max(available_cores) if available_cores else 0
        invalid_core = max_core + 1000

        with pytest.raises(ValueError) as excinfo:
            pin_to_core(invalid_core)

        assert str(invalid_core) in str(excinfo.value)
        assert "not available" in str(excinfo.value).lower()

    def test_pin_to_core_negative_raises_error(self):
        """Test that pinning to a negative core raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            pin_to_core(-1)

        assert "non-negative" in str(excinfo.value).lower()

    def test_pin_to_core_type_error(self):
        """Test that pinning with non-integer raises TypeError."""
        with pytest.raises(TypeError):
            pin_to_core("0")

    def test_pin_to_core_preserves_affinity_for_single_core(self):
        """Test that if we pin to a core, we are restricted to it."""
        available_cores = get_available_cores()
        if len(available_cores) == 1:
            # If only one core, we are already pinned
            target_core = next(iter(available_cores))
            pin_to_core(target_core)
            assert verify_pinning(target_core)
        else:
            # Pin to the first core
            target_core = min(available_cores)
            pin_to_core(target_core)
            # Verify we are restricted to exactly that one core
            current = os.sched_getaffinity(0)
            assert current == {target_core}
            assert len(current) == 1