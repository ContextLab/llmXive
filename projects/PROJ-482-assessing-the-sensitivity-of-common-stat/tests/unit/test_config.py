"""Unit tests for configuration and simulation grid generation."""
import pytest
from config import get_simulation_grid, get_test_grid


def test_get_simulation_grid_structure():
    """Verify that the simulation grid contains expected sample sizes and distributions."""
    grid = get_simulation_grid()
    
    assert isinstance(grid, list), "Simulation grid must be a list of configuration dicts"
    assert len(grid) > 0, "Simulation grid must not be empty"
    
    required_keys = {"n", "distribution", "effect_size", "test_type"}
    for config in grid:
        assert isinstance(config, dict), "Each grid item must be a dictionary"
        assert required_keys.issubset(config.keys()), f"Missing keys in config: {config}"
        assert config["n"] in [10, 50, 100, 500, 1000], f"Unexpected sample size: {config['n']}"
        assert config["distribution"] in ["normal", "uniform", "lognormal"], f"Unexpected distribution: {config['distribution']}"
        assert config["effect_size"] in [0.0, 0.5], f"Unexpected effect size: {config['effect_size']}"


def test_get_test_grid_structure():
    """Verify that the test grid contains the required statistical tests."""
    grid = get_test_grid()
    
    assert isinstance(grid, list), "Test grid must be a list"
    assert len(grid) > 0, "Test grid must not be empty"
    
    test_names = [item["name"] for item in grid]
    assert "t-test" in test_names, "t-test must be in the test grid"
    assert "anova" in test_names, "ANOVA must be in the test grid"
    assert "chi2" in test_names, "Chi-squared must be in the test grid"
