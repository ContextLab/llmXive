import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
import tempfile
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ground_truth import check_unbiased_independence, check_biased_independence, check_independence, derive_ground_truth_labels
from config import get_project_root, DataConfig

@pytest.fixture
def sample_df():
    # Create a mock dataframe with seed_id, bias_type, timestep, J_unbiased, J_biased, J_gold
    n = 100
    data = {
        'seed_id': ['seed_001'] * n,
        'bias_type': ['lexical'] * n,
        'timestep': list(range(n)),
        'J_unbiased': np.random.rand(n),
        'J_biased': np.random.rand(n),
        'J_gold': np.random.rand(n)
    }
    return pd.DataFrame(data)

def test_check_unbiased_independence_pass(sample_df):
    # Create data with low correlation
    sample_df['J_unbiased'] = np.random.rand(100)
    sample_df['J_gold'] = np.random.rand(100)
    
    passed, corr = check_unbiased_independence(sample_df, 'seed_001')
    assert passed is True
    assert abs(corr) < 0.8

def test_check_unbiased_independence_fail(sample_df):
    # Create data with high correlation
    x = np.random.rand(100)
    sample_df['J_unbiased'] = x
    sample_df['J_gold'] = x + np.random.normal(0, 0.01, 100) # High correlation
    
    passed, corr = check_unbiased_independence(sample_df, 'seed_001')
    assert passed is False
    assert corr > 0.8

def test_check_biased_independence_pass(sample_df):
    # Create data with low correlation for non-hacked phases
    # Simulate non-contaminated data
    sample_df['is_contaminated'] = False
    sample_df['J_biased'] = np.random.rand(100)
    sample_df['J_gold'] = np.random.rand(100)
    
    passed, corr = check_biased_independence(sample_df, 'seed_001')
    assert passed is True
    assert abs(corr) < 0.8

def test_check_biased_independence_fail(sample_df):
    # Create data with high correlation
    sample_df['is_contaminated'] = False
    x = np.random.rand(100)
    sample_df['J_biased'] = x
    sample_df['J_gold'] = x + np.random.normal(0, 0.01, 100)
    
    passed, corr = check_biased_independence(sample_df, 'seed_001')
    assert passed is False
    assert corr > 0.8

def test_derive_ground_truth_labels():
    # Create a dataframe with a clear drop in J_gold
    n = 200
    data = {
        'seed_id': ['seed_001'] * n,
        'bias_type': ['lexical'] * n,
        'timestep': list(range(n)),
        'J_unbiased': np.random.rand(n),
        'J_biased': np.random.rand(n),
        'J_gold': [1.0] * 50 + [0.5] * 100 + [1.0] * 50 # Drop of 0.5 over 50 steps, sustained
    }
    df = pd.DataFrame(data)
    
    df_labeled = derive_ground_truth_labels(df)
    
    # Check that labels are True in the drop region
    # The drop happens at index 50 (t=50) relative to t=0
    # We expect labels to be True from t=50 onwards for at least 3 steps
    assert df_labeled['hacked_label'].sum() > 0
    # Specifically, check the region of the drop
    drop_region = df_labeled[(df_labeled['timestep'] >= 50) & (df_labeled['timestep'] < 150)]
    assert drop_region['hacked_label'].all()

def test_check_independence_halt_on_fail(sample_df, tmp_path):
    # Mock the config to use tmp_path
    original_root = get_project_root()
    # We can't easily mock get_project_root, so we'll test the logic directly
    # Create a dataframe that fails
    fail_df = sample_df.copy()
    x = np.random.rand(100)
    fail_df['J_unbiased'] = x
    fail_df['J_gold'] = x # Perfect correlation
    
    results = check_independence(fail_df)
    assert results['status'] == 'failed'
    assert len(results['failed_seeds']) > 0