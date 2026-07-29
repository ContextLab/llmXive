"""
Tests for the ingestion module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path if running directly
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingestion import (
    validate_dgp_config,
    calculate_cronbach_alpha,
    generate_delay_discounting_data,
    generate_procrastination_data,
    generate_nback_data,
    harmonize_datasets,
    validate_core_constructs,
    handle_missing_data
)
from config import get_random_state

def test_validate_dgp_config_valid():
    config = {
        'n_participants': 100,
        'discounting_params': {'k_mean': 0.1, 'k_sigma': 0.05, 'noise_std': 0.1},
        'procrastination_params': {'n_items': 10, 'trait_mean': 0, 'trait_std': 1, 'item_noise': 0.5},
        'wm_params': {'capacity_mean': 0.5, 'capacity_std': 0.2, 'base_rt': 600, 'n_back_level': 2}
    }
    # Should not raise
    validate_dgp_config(config)

def test_validate_dgp_config_invalid():
    config = {
        'n_participants': 5, # Too small
        'discounting_params': {},
        'procrastination_params': {},
        'wm_params': {}
    }
    with pytest.raises(SystemExit):
        validate_dgp_config(config)

def test_cronbach_alpha():
    rng = get_random_state()
    n = 100
    # Create a dataframe with correlated items
    base = rng.normal(0, 1, n)
    data = {
        'item1': base + rng.normal(0, 0.1, n),
        'item2': base + rng.normal(0, 0.1, n),
        'item3': base + rng.normal(0, 0.1, n)
    }
    df = pd.DataFrame(data)
    alpha = calculate_cronbach_alpha(df, ['item1', 'item2', 'item3'])
    assert 0.5 < alpha <= 1.0, f"Alpha should be high for correlated items, got {alpha}"

def test_harmonize_datasets():
    rng = get_random_state()
    n = 50
    delay_df = generate_delay_discounting_data(n, rng, {'k_mean': 0.1, 'k_sigma': 0.05, 'noise_std': 0.1})
    proc_df = generate_procrastination_data(n, rng, {'n_items': 5, 'trait_mean': 0, 'trait_std': 1, 'item_noise': 0.5})
    nback_df = generate_nback_data(n, rng, {'capacity_mean': 0.5, 'capacity_std': 0.2, 'base_rt': 600, 'n_back_level': 2})
    
    merged = harmonize_datasets(delay_df, proc_df, nback_df)
    assert len(merged) == n
    assert 'participant_id' in merged.columns
    assert 'discount_rate_k' not in merged.columns # Not fitted yet
    assert 'procrastination_score' in merged.columns or any(c.startswith('PROC_ITEM_') for c in merged.columns)

def test_validate_core_constructs_missing():
    df = pd.DataFrame({'participant_id': ['PID_0001'], 'other_col': [1]})
    with pytest.raises(SystemExit):
        validate_core_constructs(df)

def test_handle_missing_data_reduced_model():
    # Create data with >10% missing age
    df = pd.DataFrame({
        'participant_id': [f'PID_{i:04d}' for i in range(100)],
        'age': [np.nan] * 20 + list(range(80)), # 20% missing
        'discount_rate_k': [0.1] * 100,
        'procrastination_score': [2.5] * 100,
        'wm_accuracy': [0.8] * 100
    })
    
    config_path = Path('/tmp/test_model_config.json')
    if config_path.exists(): config_path.unlink()
    
    result = handle_missing_data(df, config_path)
    
    assert 'age' not in result.columns
    assert config_path.exists()
    import json
    with open(config_path) as f:
        config = json.load(f)
    assert config['reduced_model'] is True
    assert 'age' in config['excluded_covariates']
    config_path.unlink()
    
def test_handle_missing_data_full_model():
    # Create data with <10% missing age
    df = pd.DataFrame({
        'participant_id': [f'PID_{i:04d}' for i in range(100)],
        'age': [np.nan] * 5 + list(range(95)), # 5% missing
        'discount_rate_k': [0.1] * 100,
        'procrastination_score': [2.5] * 100,
        'wm_accuracy': [0.8] * 100
    })
    
    config_path = Path('/tmp/test_model_config_full.json')
    if config_path.exists(): config_path.unlink()
    
    result = handle_missing_data(df, config_path)
    
    assert 'age' in result.columns
    assert not result['age'].isnull().any()
    assert config_path.exists()
    import json
    with open(config_path) as f:
        config = json.load(f)
    assert config['reduced_model'] is False
    config_path.unlink()
