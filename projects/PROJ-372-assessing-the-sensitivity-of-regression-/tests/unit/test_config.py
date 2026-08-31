"""
Unit tests for the configuration module.
"""
import pytest
from src.utils import config

def test_sample_size_tiers_defined():
    """Test that sample size tiers are defined and match spec requirements."""
    tiers = config.get_sample_size_tiers()
    assert isinstance(tiers, list), "Tiers must be a list"
    assert len(tiers) == 5, "There must be exactly 5 tiers"
    # Verify they are integers representing percentages
    for tier in tiers:
        assert isinstance(tier, int), f"Tier {tier} must be an integer"
        assert 0 < tier <= 100, f"Tier {tier} must be between 1 and 100"
    
    # Verify the specific values defined in spec.md
    assert tiers == [10, 25, 50, 75, 90], "Tiers must match the spec: [10, 25, 50, 75, 90]"

def test_num_subsets_per_tier():
    """Test that the number of subsets per tier is configured."""
    count = config.get_num_subsets_per_tier()
    assert isinstance(count, int)
    assert count > 0

def test_convergence_threshold():
    """Test that convergence threshold is a valid percentage."""
    threshold = config.get_convergence_threshold()
    assert isinstance(threshold, (int, float))
    assert 0 < threshold < 100

def test_random_seed():
    """Test that a random seed is configured."""
    seed = config.get_random_seed()
    assert isinstance(seed, int)
    assert seed >= 0
