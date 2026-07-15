"""
Tests for src/config/settings.py
"""
import os
import pytest
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.settings import (
    get_fidelity_threshold,
    PATHS,
    SEEDS,
    HYPERPARAMETERS,
    ensure_dirs,
    get_path,
    _DEFAULT_FIDELITY_THRESHOLD,
)


class TestFidelityThreshold:
    """Tests for the fidelity_threshold configuration logic."""

    def test_default_value(self):
        """Test that the default value is returned when env var is not set."""
        # Ensure env var is not set
        if "LMMXIVE_FIDELITY_THRESHOLD" in os.environ:
            del os.environ["LMMXIVE_FIDELITY_THRESHOLD"]
        
        # Reload the function logic (since it reads env at call time)
        # We can't easily reload the module without side effects, 
        # but we can test the logic by mocking or just relying on the function's behavior.
        # Since the function reads os.getenv directly, we just need to ensure env is clean.
        val = get_fidelity_threshold()
        assert isinstance(val, float)
        assert val == _DEFAULT_FIDELITY_THRESHOLD

    def test_env_override_valid(self):
        """Test that a valid environment variable overrides the default."""
        os.environ["LMMXIVE_FIDELITY_THRESHOLD"] = "0.9"
        try:
            val = get_fidelity_threshold()
            assert val == 0.9
        finally:
            del os.environ["LMMXIVE_FIDELITY_THRESHOLD"]

    def test_env_override_invalid_type(self):
        """Test that a non-numeric env var raises ValueError."""
        os.environ["LMMXIVE_FIDELITY_THRESHOLD"] = "not_a_number"
        try:
            with pytest.raises(ValueError, match="Invalid value"):
                get_fidelity_threshold()
        finally:
            del os.environ["LMMXIVE_FIDELITY_THRESHOLD"]

    def test_env_override_out_of_range_low(self):
        """Test that a value < 0.0 raises ValueError."""
        os.environ["LMMXIVE_FIDELITY_THRESHOLD"] = "-0.1"
        try:
            with pytest.raises(ValueError, match="between 0.0 and 1.0"):
                get_fidelity_threshold()
        finally:
            del os.environ["LMMXIVE_FIDELITY_THRESHOLD"]

    def test_env_override_out_of_range_high(self):
        """Test that a value > 1.0 raises ValueError."""
        os.environ["LMMXIVE_FIDELITY_THRESHOLD"] = "1.5"
        try:
            with pytest.raises(ValueError, match="between 0.0 and 1.0"):
                get_fidelity_threshold()
        finally:
            del os.environ["LMMXIVE_FIDELITY_THRESHOLD"]

    def test_boundary_values(self):
        """Test that 0.0 and 1.0 are accepted."""
        for val in ["0.0", "1.0"]:
            os.environ["LMMXIVE_FIDELITY_THRESHOLD"] = val
            try:
                result = get_fidelity_threshold()
                assert result == float(val)
            finally:
                del os.environ["LMMXIVE_FIDELITY_THRESHOLD"]


class TestPaths:
    """Tests for path configuration."""

    def test_paths_exist(self):
        """Verify that all expected path keys exist."""
        required_keys = ["root", "src", "data", "data_processed", "data_results"]
        for key in required_keys:
            assert key in PATHS, f"Key '{key}' missing from PATHS"

    def test_paths_are_absolute(self):
        """Verify that all paths are absolute."""
        for key, path in PATHS.items():
            if isinstance(path, Path):
                assert path.is_absolute(), f"Path '{key}' is not absolute: {path}"

    def test_get_path_valid(self):
        """Test get_path with a valid key."""
        p = get_path("root")
        assert isinstance(p, Path)

    def test_get_path_invalid(self):
        """Test get_path with an invalid key raises KeyError."""
        with pytest.raises(KeyError):
            get_path("non_existent_key")


class TestHyperparameters:
    """Tests for hyperparameters configuration."""

    def test_target_dimensions(self):
        """Verify the target dimensions list is correct."""
        expected = [16, 32, 64, 128, 256]
        assert HYPERPARAMETERS["target_dimensions"] == expected

    def test_batch_size_cpu_optimized(self):
        """Verify batch size is set to 1 for CPU optimization."""
        assert HYPERPARAMETERS["batch_size"] == 1

    def test_global_timeout(self):
        """Verify global timeout is 6 hours (21600 seconds)."""
        assert HYPERPARAMETERS["global_timeout_seconds"] == 21600


class TestSeeds:
    """Tests for seed configuration."""

    def test_seed_types(self):
        """Verify all seeds are integers."""
        for key, val in SEEDS.items():
            assert isinstance(val, int), f"Seed '{key}' is not an integer"

    def test_global_seed(self):
        """Verify global seed is 42."""
        assert SEEDS["global"] == 42
