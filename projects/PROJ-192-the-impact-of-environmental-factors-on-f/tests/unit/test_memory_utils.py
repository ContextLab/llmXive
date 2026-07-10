"""
Unit tests for memory-safe subsampling logic (T014a).
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from utils.memory import (
    get_current_ram_usage_gb,
    check_ram_and_subsample,
    estimate_dataframe_memory_mb,
    RAM_LIMIT_GB
)


def test_get_current_ram_usage_gb():
    """Test that RAM usage function returns a positive float."""
    ram = get_current_ram_usage_gb()
    assert isinstance(ram, float)
    assert ram > 0


def test_estimate_dataframe_memory_mb():
    """Test memory estimation of a DataFrame."""
    df = pd.DataFrame({'a': [1] * 1000, 'b': ['x'] * 1000})
    mem_mb = estimate_dataframe_memory_mb(df)
    assert mem_mb > 0


@patch('utils.memory.get_current_ram_usage_gb')
def test_no_subsampling_under_limit(mock_ram):
    """Test that no subsampling occurs when RAM is under the limit."""
    mock_ram.return_value = 4.0  # 4GB < 6GB limit
    
    df = pd.DataFrame({'sample_id': range(100), 'value': range(100)})
    result, ratio, was_subsampled = check_ram_and_subsample(df, 'value')
    
    assert was_subsampled is False
    assert ratio == 1.0
    assert len(result) == len(df)


@patch('utils.memory.get_current_ram_usage_gb')
def test_subsampling_triggered_over_limit(mock_ram):
    """Test that subsampling is triggered when RAM exceeds the limit."""
    mock_ram.return_value = 8.0  # 8GB > 6GB limit
    
    df = pd.DataFrame({
        'sample_id': range(1000), 
        'value': range(1000)
    })
    
    # Force a specific ratio for deterministic testing
    result, ratio, was_subsampled = check_ram_and_subsample(
        df, 'value', force_ratio=0.5
    )
    
    assert was_subsampled is True
    assert ratio == 0.5
    assert len(result) == 500


@patch('utils.memory.get_current_ram_usage_gb')
def test_stratified_subsampling(mock_ram):
    """Test stratified subsampling preserves group structure."""
    mock_ram.return_value = 8.0  # Trigger subsampling
    
    df = pd.DataFrame({
        'biome': ['forest'] * 500 + ['grassland'] * 500,
        'value': range(1000)
    })
    
    result, ratio, was_subsampled = check_ram_and_subsample(
        df, 'value', group_column='biome', force_ratio=0.4
    )
    
    assert was_subsampled is True
    assert len(result) == 400
    assert result['biome'].value_counts()['forest'] == 200
    assert result['biome'].value_counts()['grassland'] == 200


@patch('utils.memory.get_current_ram_usage_gb')
def test_min_samples_per_group_enforced(mock_ram):
    """Test that min_samples_per_group is respected."""
    mock_ram.return_value = 8.0
    
    # Create a small group that would be undersampled by ratio
    df = pd.DataFrame({
        'biome': ['rare'] * 5 + ['common'] * 1000,
        'value': range(1005)
    })
    
    result, ratio, was_subsampled = check_ram_and_subsample(
        df, 'value', group_column='biome', 
        min_samples_per_group=5, force_ratio=0.1
    )
    
    # The 'rare' group should keep all 5 samples (min threshold)
    assert result[result['biome'] == 'rare']['value'].count() == 5
    assert len(result) > 100 # Common group should be subsampled but 'rare' kept full
