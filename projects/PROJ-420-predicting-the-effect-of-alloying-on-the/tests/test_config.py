"""
Unit tests for the new configuration constants.

These tests verify that importing ``code.config`` provides the
expected module‑level constants and that the ``Config`` singleton
exposes compatible attributes.
"""

import pathlib

import pytest

from code import config

def test_module_constants_exist():
    """Check that the required top‑level constants are defined."""
    assert isinstance(config.DATA_ROOT, pathlib.Path)
    assert isinstance(config.MODEL_ROOT, pathlib.Path)
    assert isinstance(config.RESULT_ROOT, pathlib.Path)
    assert isinstance(config.RANDOM_SEED, int)
    assert isinstance(config.VALID_MEASUREMENT_METHODS, list)
    # The list should contain the expected regex strings.
    expected = {r"(?i)ultrasonic", r"(?i)direct", r"(?i)resonant", r"(?i)impulse"}
    assert set(config.VALID_MEASUREMENT_METHODS) == expected

def test_config_singleton_attributes():
    """Legacy attribute access (e.g., CONFIG.results) must work."""
    cfg = config.get_config()
    # Alias for results_dir
    assert cfg.results == cfg.results_dir
    # Random seed should match the module constant
    assert cfg.random_seed == config.RANDOM_SEED
    # Measurement methods list should be identical
    assert cfg.VALID_MEASUREMENT_METHODS == config.VALID_MEASUREMENT_METHODS