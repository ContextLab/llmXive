"""
Unit tests for code/config.py.

Verifies:
1. Deterministic seeds are set correctly.
2. Path helpers return correct absolute paths.
3. Step limit enforcement works as expected.
4. RAM limit check does not crash.
"""
import os
import random
import numpy as np
import torch
import pytest
from pathlib import Path
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import (
    set_deterministic_seeds,
    get_project_root,
    get_data_path,
    get_benchmark_path,
    get_result_path,
    enforce_step_limit,
    StepLimitExceeded,
    MAX_STEPS,
    SEED,
    RAM_LIMIT_GB,
)


class TestSeeds:
    """Tests for deterministic seed setting."""

    def test_seed_determinism(self):
        """Verify that setting the seed produces reproducible results."""
        # Reset seeds
        set_deterministic_seeds(12345)
        val1 = random.random()
        arr1 = np.random.rand(5)
        t1 = torch.rand(5)

        # Reset seeds again
        set_deterministic_seeds(12345)
        val2 = random.random()
        arr2 = np.random.rand(5)
        t2 = torch.rand(5)

        assert val1 == val2
        np.testing.assert_array_equal(arr1, arr2)
        torch.testing.assert_close(t1, t2)

    def test_default_seed(self):
        """Verify default seed is used if no override provided."""
        # This test assumes the environment variable isn't set to a different value
        # For robust testing, we'd mock os.environ, but this is a sanity check
        set_deterministic_seeds()
        val = random.random()
        
        # Reset and check again
        set_deterministic_seeds()
        val2 = random.random()
        
        assert val == val2


class TestPaths:
    """Tests for path helper functions."""

    def test_project_root(self):
        """Verify project root is the parent of the code directory."""
        root = get_project_root()
        assert root.name == "llmXive-follow-up-extending-video2gui-sy" or root.name == "project" # Flexible check
        assert (root / "code").exists()

    def test_data_path(self):
        """Verify data path construction."""
        p = get_data_path("benchmarks/test.json")
        assert p == get_project_root() / "data" / "benchmarks" / "test.json"

    def test_benchmark_path(self):
        """Verify benchmark path construction."""
        p = get_benchmark_path("benchmark.json")
        assert p == get_project_root() / "data" / "benchmarks" / "benchmark.json"

    def test_result_path(self):
        """Verify result path construction."""
        p = get_result_path("stats.json")
        assert p == get_project_root() / "data" / "results" / "stats.json"


class TestStepLimit:
    """Tests for step limit enforcement."""

    def test_within_limit(self):
        """Verify no exception is raised within limit."""
        # Should not raise
        enforce_step_limit(1)
        enforce_step_limit(49)
        enforce_step_limit(MAX_STEPS)

    def test_exceeds_limit(self):
        """Verify exception is raised when limit is exceeded."""
        with pytest.raises(StepLimitExceeded):
            enforce_step_limit(MAX_STEPS + 1)

        with pytest.raises(StepLimitExceeded):
            enforce_step_limit(100)

    def test_limit_constant(self):
        """Verify MAX_STEPS constant is 50."""
        assert MAX_STEPS == 50


class TestRamLimit:
    """Tests for RAM limit configuration."""

    def test_ram_limit_constant(self):
        """Verify RAM_LIMIT_GB constant is 7.0."""
        assert RAM_LIMIT_GB == 7.0
