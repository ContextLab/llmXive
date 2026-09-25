"""
Tests for T023b: Data splitting logic.

Verifies that:
1. Splits are deterministic given the same seed
2. Training and validation sets are disjoint
3. All episode indices are accounted for
4. Split ratios are correct
5. Output file is valid JSON with expected structure
"""
import os
import json
import pytest
import random
import numpy as np
from typing import Dict, List, Any

from config import get_seed, set_seed, EPISODES_PER_SETTING
from experiments.split_data import (
    split_episodes_for_setting,
    run_data_splitting,
    save_validation_config,
    ValidationSetConfig,
    VALIDATION_SPLIT_RATIO
)


@pytest.fixture
def temp_output_path(tmp_path):
    """Create a temporary output path for testing."""
    return str(tmp_path / "validation_set_config.json")


def test_split_episodes_deterministic():
    """Test that splitting is deterministic with the same seed."""
    tier = 1
    threshold = 0.5
    seed = 42
    total_episodes = 1000
    
    # First split
    random.seed(seed)
    np.random.seed(seed)
    train1, val1 = split_episodes_for_setting(tier, threshold, seed, total_episodes)
    
    # Second split with same parameters
    train2, val2 = split_episodes_for_setting(tier, threshold, seed, total_episodes)
    
    assert train1 == train2, "Training indices should be identical"
    assert val1 == val2, "Validation indices should be identical"


def test_split_episodes_disjoint():
    """Test that training and validation sets are disjoint."""
    tier = 2
    threshold = 0.3
    seed = 123
    total_episodes = 1000
    
    train, val = split_episodes_for_setting(tier, threshold, seed, total_episodes)
    
    # Check no overlap
    assert set(train).isdisjoint(set(val)), "Training and validation sets should be disjoint"


def test_split_episodes_complete():
    """Test that all episode indices are accounted for."""
    tier = 3
    threshold = 0.7
    seed = 456
    total_episodes = 1000
    
    train, val = split_episodes_for_setting(tier, threshold, seed, total_episodes)
    
    all_indices = set(range(total_episodes))
    split_indices = set(train) | set(val)
    
    assert all_indices == split_indices, "All indices should be in either train or validation"


def test_split_episodes_ratio():
    """Test that split ratios are approximately correct."""
    tier = 1
    threshold = 0.0
    seed = 789
    total_episodes = 1000
    
    train, val = split_episodes_for_setting(tier, threshold, seed, total_episodes)
    
    expected_val_size = int(total_episodes * VALIDATION_SPLIT_RATIO)
    expected_train_size = total_episodes - expected_val_size
    
    assert len(val) == expected_val_size, f"Validation size should be {expected_val_size}"
    assert len(train) == expected_train_size, f"Training size should be {expected_train_size}"


def test_split_episodes_different_tiers_different_seeds():
    """Test that different tiers/thresholds produce different splits."""
    seed = 42
    total_episodes = 1000
    
    # Split for tier 1, threshold 0.0
    train1, val1 = split_episodes_for_setting(1, 0.0, seed, total_episodes)
    
    # Split for tier 2, threshold 0.0 (different tier seed)
    train2, val2 = split_episodes_for_setting(2, 0.0, seed, total_episodes)
    
    # Should be different due to seed derivation
    assert train1 != train2 or val1 != val2, "Different tiers should produce different splits"


def test_run_data_splitting_structure(temp_output_path):
    """Test that run_data_splitting produces correct structure."""
    config = run_data_splitting()
    
    assert isinstance(config, ValidationSetConfig)
    assert config.seed == get_seed()
    assert config.validation_ratio == VALIDATION_SPLIT_RATIO
    assert config.total_episodes_per_setting == EPISODES_PER_SETTING
    assert len(config.splits) > 0
    
    # Check each split has required fields
    required_fields = [
        'tier', 'threshold', 'training_indices', 'validation_indices',
        'total_episodes', 'training_size', 'validation_size'
    ]
    
    for split in config.splits:
        for field in required_fields:
            assert field in split, f"Split missing field: {field}"


def test_save_validation_config(temp_output_path):
    """Test that save_validation_config writes valid JSON."""
    config = run_data_splitting()
    save_validation_config(config, temp_output_path)
    
    # Check file exists
    assert os.path.exists(temp_output_path), "Output file should exist"
    
    # Check valid JSON
    with open(temp_output_path, 'r') as f:
        loaded_config = json.load(f)
    
    assert 'seed' in loaded_config
    assert 'validation_ratio' in loaded_config
    assert 'total_episodes_per_setting' in loaded_config
    assert 'splits' in loaded_config
    assert len(loaded_config['splits']) > 0


def test_save_validation_config_content(temp_output_path):
    """Test that saved config has correct values."""
    config = run_data_splitting()
    save_validation_config(config, temp_output_path)
    
    with open(temp_output_path, 'r') as f:
        loaded_config = json.load(f)
    
    # Verify key values
    assert loaded_config['seed'] == get_seed()
    assert loaded_config['validation_ratio'] == VALIDATION_SPLIT_RATIO
    assert loaded_config['total_episodes_per_setting'] == EPISODES_PER_SETTING
    
    # Verify split sizes
    for split in loaded_config['splits']:
        expected_val_size = int(EPISODES_PER_SETTING * VALIDATION_SPLIT_RATIO)
        expected_train_size = EPISODES_PER_SETTING - expected_val_size
        
        assert split['validation_size'] == expected_val_size
        assert split['training_size'] == expected_train_size
        assert split['total_episodes'] == EPISODES_PER_SETTING
        
        # Verify index counts match sizes
        assert len(split['training_indices']) == split['training_size']
        assert len(split['validation_indices']) == split['validation_size']


def test_all_tiers_covered():
    """Test that all tiers (1, 2, 3) are included in splits."""
    config = run_data_splitting()
    
    tiers_in_config = set(split['tier'] for split in config.splits)
    expected_tiers = {1, 2, 3}
    
    assert tiers_in_config == expected_tiers, f"Missing tiers: {expected_tiers - tiers_in_config}"


def test_all_thresholds_covered():
    """Test that all thresholds (0.0 to 1.0 in 0.1 steps) are included."""
    config = run_data_splitting()
    
    thresholds_in_config = sorted(set(split['threshold'] for split in config.splits))
    expected_thresholds = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    
    assert thresholds_in_config == expected_thresholds, \
        f"Missing thresholds: {set(expected_thresholds) - set(thresholds_in_config)}"


def test_total_combinations():
    """Test that we have the correct number of (tier, threshold) combinations."""
    config = run_data_splitting()
    
    expected_combinations = 3 * 11  # 3 tiers × 11 thresholds
    assert len(config.splits) == expected_combinations, \
        f"Expected {expected_combinations} combinations, got {len(config.splits)}"