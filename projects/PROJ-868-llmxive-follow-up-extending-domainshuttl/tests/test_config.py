"""
Tests for src/config/settings.py
"""
import pytest
import sys
from pathlib import Path

# Add src to path for imports if running from root
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.settings import (
    get_fidelity_threshold,
    get_seed,
    get_path,
    get_hyperparameter,
    validate_config,
    HYPERPARAMETERS,
    SEEDS,
    PATHS
)

class TestFidelityThreshold:
    def test_get_fidelity_threshold_returns_float(self):
        """Test that the threshold is returned as a float."""
        threshold = get_fidelity_threshold()
        assert isinstance(threshold, float)
        assert 0.0 < threshold <= 1.0

    def test_fidelity_threshold_default_exists(self):
        """Test that a default fallback exists and is valid."""
        # Should not raise
        val = get_fidelity_threshold()
        assert val is not None

class TestSeeds:
    def test_get_seed_returns_int(self):
        """Test that seeds are integers."""
        seed = get_seed("global")
        assert isinstance(seed, int)
        assert seed == 42

    def test_get_seed_invalid_name_raises(self):
        """Test that requesting an unknown seed raises KeyError."""
        with pytest.raises(KeyError):
            get_seed("non_existent_seed")

class TestPaths:
    def test_get_path_returns_path_object(self):
        """Test that paths are Path objects."""
        p = get_path("processed")
        assert isinstance(p, Path)

    def test_get_path_invalid_key_raises(self):
        """Test that requesting an unknown path raises KeyError."""
        with pytest.raises(KeyError):
            get_path("non_existent_path")

class TestHyperparameters:
    def test_get_hyperparameter_returns_value(self):
        """Test retrieving a known hyperparameter."""
        val = get_hyperparameter("num_subjects")
        assert val == 100

    def test_get_hyperparameter_default_fallback(self):
        """Test default fallback for unknown key."""
        val = get_hyperparameter("unknown_key", default="fallback")
        assert val == "fallback"

class TestValidation:
    def test_validate_config_passes(self):
        """Test that validate_config returns True for valid config."""
        assert validate_config() is True

    def test_validate_config_checks_threshold(self):
        """Test that validation ensures threshold is valid."""
        # This relies on the global validation in settings.py
        # If the global state is valid, this should pass.
        assert validate_config() is True
