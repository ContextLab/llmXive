"""
Tests for the data ingestion pipeline.
"""

import pytest
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from ingestion import (
    validate_dgp_config,
    generate_delay_discounting_data,
    generate_procrastination_data,
    generate_nback_data,
    calculate_cronbach_alpha,
    harmonize_datasets,
    DGP_DEFAULTS
)

@pytest.fixture
def random_seed():
    return 42

@pytest.fixture
def data_path():
    return Path(__file__).parent.parent / 'data'

def test_dgp_params_valid():
    """Test that DGP parameters are valid."""
    assert validate_dgp_config(DGP_DEFAULTS) is True

    # Test invalid config
    invalid_config = DGP_DEFAULTS.copy()
    del invalid_config['k_mean']
    assert validate_dgp_config(invalid_config) is False

def test_generate_delay_discounting_data(random_seed):
    """Test delay discounting data generation."""
    n = 100
    df = generate_delay_discounting_data(n, random_seed)

    assert len(df) == n * 5  # 5 delays per participant
    assert 'participant_id' in df.columns
    assert 'delay' in df.columns
    assert 'amount' in df.columns
    assert 'choice' in df.columns
    assert 'k_true' in df.columns
    assert df['choice'].isin([0, 1]).all()

def test_generate_procrastination_data(random_seed):
    """Test procrastination data generation."""
    n = 100
    df = generate_procrastination_data(n, random_seed)

    assert len(df) == n
    assert 'participant_id' in df.columns
    for i in range(1, 11):
        assert f'procrastination_item_{i}' in df.columns
        assert df[f'procrastination_item_{i}'].between(1, 5).all()

def test_generate_nback_data(random_seed):
    """Test n-back data generation."""
    n = 100
    df = generate_nback_data(n, random_seed)

    assert len(df) == n
    assert 'participant_id' in df.columns
    assert 'nback_accuracy' in df.columns
    assert 'nback_rt' in df.columns
    assert df['nback_accuracy'].between(0.5, 1.0).all()
    assert df['nback_rt'].between(300, 2000).all()

def test_cronbach_alpha():
    """Test Cronbach's alpha calculation."""
    # Create synthetic data with known reliability
    np.random.seed(42)
    n = 100
    data = np.random.randn(n, 5) * 0.5 + 3  # 5 items, moderate correlation
    df = pd.DataFrame(data, columns=['item1', 'item2', 'item3', 'item4', 'item5'])

    alpha = calculate_cronbach_alpha(df, ['item1', 'item2', 'item3', 'item4', 'item5'])
    assert 0 <= alpha <= 1

def test_harmonization_id_match(random_seed):
    """Test that harmonization preserves participant IDs correctly."""
    n = 100
    delay_df = generate_delay_discounting_data(n, random_seed)
    proc_df = generate_procrastination_data(n, random_seed)
    nback_df = generate_nback_data(n, random_seed)

    merged = harmonize_datasets(delay_df, proc_df, nback_df)

    assert len(merged) == n
    assert 'procrastination_score' in merged.columns
    assert 'wm_accuracy' in merged.columns
    assert 'discount_rate_k' in merged.columns