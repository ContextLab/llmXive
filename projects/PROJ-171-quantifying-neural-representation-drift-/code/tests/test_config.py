"""
Basic sanity tests for the configuration module.
"""
import pytest

from code.src import config

def test_config_defaults():
    """Ensure the CONFIG singleton exposes the expected defaults."""
    assert config.CONFIG.primary_model == "linear"
    assert isinstance(config.CONFIG.random_seed, int)
    assert config.CONFIG.random_seed == 42

def test_config_immutable():
    """The Config dataclass should be frozen."""
    with pytest.raises(AttributeError):
        # Attempting to modify a frozen dataclass raises AttributeError
        config.CONFIG.primary_model = "exponential"
