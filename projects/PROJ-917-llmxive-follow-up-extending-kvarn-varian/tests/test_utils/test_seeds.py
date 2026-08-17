"""
Unit tests for global random seed management.

Verifies that set_global_seed correctly initializes seeds for
random, numpy, and torch (if available), and that the same seed
produces deterministic results.
"""
import random
import hashlib
import json
import tempfile
from pathlib import Path

import pytest
import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.seeds import (
    set_global_seed,
    get_seed,
    reset_seed,
    ensure_seed_set,
    get_seed_info
)


class TestSeedManagement:
    """Tests for seed management functions."""

    def test_set_global_seed_types(self):
        """Test that set_global_seed rejects non-integer seeds."""
        reset_seed()
        with pytest.raises(TypeError):
            set_global_seed("42")
        with pytest.raises(TypeError):
            set_global_seed(42.5)

    def test_set_global_seed_functionality(self):
        """Test that set_global_seed actually sets the seeds."""
        seed_val = 12345
        set_global_seed(seed_val)

        # Check global state
        assert get_seed() == seed_val
        info = get_seed_info()
        assert info["seed"] == seed_val
        assert info["is_set"] is True

    def test_reset_seed(self):
        """Test that reset_seed clears the global state."""
        set_global_seed(42)
        reset_seed()
        assert get_seed() is None
        assert get_seed_info()["is_set"] is False

    def test_ensure_seed_set(self):
        """Test that ensure_seed_set sets a default if none exists."""
        reset_seed()
        default = 999
        result = ensure_seed_set(default)
        assert result == default
        assert get_seed() == default

    def test_deterministic_numpy(self):
        """Test that numpy generates the same sequence with the same seed."""
        seed = 42
        set_global_seed(seed)
        arr1 = np.random.rand(10)

        set_global_seed(seed)
        arr2 = np.random.rand(10)

        np.testing.assert_array_equal(arr1, arr2)

    def test_deterministic_random(self):
        """Test that random module generates the same sequence with the same seed."""
        seed = 42
        set_global_seed(seed)
        rand1 = [random.random() for _ in range(10)]

        set_global_seed(seed)
        rand2 = [random.random() for _ in range(10)]

        assert rand1 == rand2

    @pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
    def test_deterministic_torch(self):
        """Test that torch generates the same sequence with the same seed."""
        seed = 42
        set_global_seed(seed)
        t1 = torch.rand(10)

        set_global_seed(seed)
        t2 = torch.rand(10)

        torch.testing.assert_close(t1, t2)

    def test_deterministic_end_to_end(self):
        """
        End-to-end test: Run a simple generation process twice with the same seed
        and verify the output checksums match.
        """
        def generate_test_data(seed: int) -> bytes:
            """Simulate a data generation process."""
            set_global_seed(seed)
            data = {
                "np_array": np.random.rand(100).tolist(),
                "rand_val": random.random(),
                "np_sum": float(np.sum(np.random.rand(50)))
            }
            # Convert to JSON string and hash for checksum
            json_str = json.dumps(data, sort_keys=True)
            return hashlib.sha256(json_str.encode()).digest()

        seed = 54321
        checksum1 = generate_test_data(seed)
        checksum2 = generate_test_data(seed)

        assert checksum1 == checksum2, "Determinism failed: checksums do not match"

    def test_different_seeds_produce_different_results(self):
        """Verify that different seeds produce different outputs."""
        data1 = []
        data2 = []

        set_global_seed(1)
        for _ in range(5):
            data1.append(random.random())

        set_global_seed(2)
        for _ in range(5):
            data2.append(random.random())

        assert data1 != data2, "Different seeds should produce different sequences"