"""
Tests for data splitting logic.
"""
import os
import json
import pytest
import random
import numpy as np
from typing import Dict, List, Any

from experiments.split_data import (
    SplitConfig,
    ValidationSetConfig,
    split_episodes_for_setting,
    run_data_splitting,
    save_validation_config
)
from config import get_seed, set_seed


@pytest.fixture
def temp_output_path(tmp_path):
    """Create a temporary output path for tests."""
    output_dir = tmp_path / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir / "validation_set_config.json")


def test_split_episodes_deterministic():
    """Test that splitting with the same seed produces identical results."""
    config = SplitConfig(validation_ratio=0.2, seed=42)
    
    split1 = split_episodes_for_setting(1, 0.5, 1000, config)
    split2 = split_episodes_for_setting(1, 0.5, 1000, config)
    
    assert split1.train_indices == split2.train_indices
    assert split1.val_indices == split2.val_indices


def test_split_episodes_disjoint():
    """Test that train and validation indices are disjoint."""
    config = SplitConfig(validation_ratio=0.2, seed=42)
    split = split_episodes_for_setting(1, 0.5, 1000, config)
    
    train_set = set(split.train_indices)
    val_set = set(split.val_indices)
    
    assert train_set.isdisjoint(val_set)


def test_split_episodes_complete():
    """Test that train and validation indices cover all episodes."""
    config = SplitConfig(validation_ratio=0.2, seed=42)
    split = split_episodes_for_setting(1, 0.5, 1000, config)
    
    all_indices = set(range(1000))
    combined = set(split.train_indices) | set(split.val_indices)
    
    assert all_indices == combined


def test_split_episodes_ratio():
    """Test that the validation ratio is approximately correct."""
    config = SplitConfig(validation_ratio=0.2, seed=42)
    split = split_episodes_for_setting(1, 0.5, 1000, config)
    
    expected_val_size = int(1000 * 0.2)
    assert split.val_size == expected_val_size
    assert split.train_size == 1000 - expected_val_size


def test_split_episodes_different_tiers_different_seeds():
    """Test that different tiers or seeds produce different splits."""
    config1 = SplitConfig(validation_ratio=0.2, seed=42)
    config2 = SplitConfig(validation_ratio=0.2, seed=43)
    
    split1 = split_episodes_for_setting(1, 0.5, 1000, config1)
    split2 = split_episodes_for_setting(1, 0.5, 1000, config2)
    
    # Different seeds should produce different splits (with high probability)
    assert split1.val_indices != split2.val_indices


def test_run_data_splitting_structure():
    """Test that run_data_splitting produces the correct structure."""
    tiers = [1, 2]
    thresholds = [0.0, 0.5, 1.0]
    episodes_per_setting = 100
    
    splits = run_data_splitting(
        tiers=tiers,
        thresholds=thresholds,
        episodes_per_setting=episodes_per_setting,
        validation_ratio=0.2,
        seed=42
    )
    
    expected_keys = len(tiers) * len(thresholds)
    assert len(splits) == expected_keys
    
    for key, split in splits.items():
        assert split.total_episodes == episodes_per_setting
        assert split.val_size == int(episodes_per_setting * 0.2)
        assert split.train_size == episodes_per_setting - split.val_size


def test_save_validation_config(temp_output_path):
    """Test that save_validation_config writes valid JSON."""
    tiers = [1, 2]
    thresholds = [0.0, 0.5]
    episodes_per_setting = 100
    
    splits = run_data_splitting(
        tiers=tiers,
        thresholds=thresholds,
        episodes_per_setting=episodes_per_setting,
        validation_ratio=0.2,
        seed=42
    )
    
    save_validation_config(splits, temp_output_path)
    
    # Verify file exists and is valid JSON
    assert os.path.exists(temp_output_path)
    with open(temp_output_path, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, dict)
    assert len(data) == len(splits)


def test_save_validation_config_content(temp_output_path):
    """Test that the saved config contains all required fields."""
    tiers = [1]
    thresholds = [0.5]
    episodes_per_setting = 100
    
    splits = run_data_splitting(
        tiers=tiers,
        thresholds=thresholds,
        episodes_per_setting=episodes_per_setting,
        validation_ratio=0.2,
        seed=42
    )
    
    save_validation_config(splits, temp_output_path)
    
    with open(temp_output_path, 'r') as f:
        data = json.load(f)
    
    key = "tier_1_threshold_0.5"
    assert key in data
    
    config = data[key]
    required_fields = [
        'tier', 'threshold', 'total_episodes', 
        'train_indices', 'val_indices', 'val_size', 'train_size'
    ]
    
    for field in required_fields:
        assert field in config


def test_all_tiers_covered():
    """Test that all tiers (1, 2, 3) are covered."""
    tiers = [1, 2, 3]
    thresholds = [0.0, 0.5, 1.0]
    
    splits = run_data_splitting(
        tiers=tiers,
        thresholds=thresholds,
        episodes_per_setting=100,
        validation_ratio=0.2,
        seed=42
    )
    
    for tier in tiers:
        for threshold in thresholds:
            key = f"tier_{tier}_threshold_{threshold:.1f}"
            assert key in splits


def test_all_thresholds_covered():
    """Test that all thresholds from 0.0 to 1.0 in 0.1 steps are covered."""
    tiers = [1]
    thresholds = np.arange(0.0, 1.01, 0.1).tolist()
    
    splits = run_data_splitting(
        tiers=tiers,
        thresholds=thresholds,
        episodes_per_setting=100,
        validation_ratio=0.2,
        seed=42
    )
    
    for threshold in thresholds:
        key = f"tier_1_threshold_{threshold:.1f}"
        assert key in splits


def test_total_combinations():
    """Test the total number of combinations for the full experiment."""
    tiers = [1, 2, 3]
    thresholds = np.arange(0.0, 1.01, 0.1).tolist()
    
    splits = run_data_splitting(
        tiers=tiers,
        thresholds=thresholds,
        episodes_per_setting=1000,
        validation_ratio=0.2,
        seed=42
    )
    
    expected_combinations = len(tiers) * len(thresholds)
    assert len(splits) == expected_combinations
    
    # Verify each split has the correct episode count
    for split in splits.values():
        assert split.total_episodes == 1000
        assert split.val_size == 200
        assert split.train_size == 800