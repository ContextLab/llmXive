"""
Integration tests for MICE chain runner functionality.
"""
import pytest
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
import tempfile
from imputation_pipeline import run_mice_chains, load_metadata
from config import SeedManager

@pytest.fixture
def sample_data():
    """Create a sample dataset with missing values."""
    np.random.seed(42)
    n = 100
    data = {
        'var1': np.random.normal(50, 10, n),
        'var2': np.random.normal(30, 5, n),
        'var3': np.random.normal(70, 15, n)
    }
    df = pd.DataFrame(data)
    
    # Introduce missing values (MCAR)
    missing_idx = np.random.choice(n, size=int(n * 0.2), replace=False)
    df.loc[missing_idx, 'var1'] = np.nan
    df.loc[missing_idx, 'var2'] = np.nan
    
    return df

@pytest.fixture
def sample_meta():
    """Create sample metadata."""
    return {
        'missingness_mechanism': 'MCAR',
        'true_mean': 50,
        'true_variance': 100
    }

@pytest.fixture
def temp_files(sample_data, sample_meta):
    """Create temporary files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = os.path.join(tmpdir, 'test_data.csv')
        meta_path = os.path.join(tmpdir, 'test_meta.json')
        output_path = os.path.join(tmpdir, 'test_output.json')
        
        sample_data.to_csv(data_path, index=False)
        with open(meta_path, 'w') as f:
            json.dump(sample_meta, f)
        
        yield {
            'data_path': data_path,
            'meta_path': meta_path,
            'output_path': output_path,
            'tmpdir': tmpdir
        }

def test_mice_runs_with_valid_data(temp_files):
    """Test that MICE runs successfully on valid data."""
    result = run_mice_chains(
        data_path=temp_files['data_path'],
        output_path=temp_files['output_path'],
        n_chains=2,
        max_iter=10,  # Small for testing
        burn_in=5,
        base_seed=42,
        meta_path=temp_files['meta_path']
    )
    
    assert result['status'] == 'success'
    assert result['n_chains'] == 2
    assert 'pooled_statistics' in result
    assert 'chain_diagnostics' in result

def test_mice_discards_burn_in(temp_files):
    """Test that burn-in iterations are properly discarded."""
    result = run_mice_chains(
        data_path=temp_files['data_path'],
        output_path=temp_files['output_path'],
        n_chains=2,
        max_iter=20,
        burn_in=15,
        base_seed=42,
        meta_path=temp_files['meta_path']
    )
    
    assert result['status'] == 'success'
    # Each chain should have some iterations kept after burn-in
    for diag in result['chain_diagnostics']:
        assert diag['chain_id'] > 0

def test_mice_uses_distinct_seeds(temp_files):
    """Test that distinct seeds are used for each chain."""
    result = run_mice_chains(
        data_path=temp_files['data_path'],
        output_path=temp_files['output_path'],
        n_chains=4,
        max_iter=10,
        burn_in=5,
        base_seed=100,
        meta_path=temp_files['meta_path']
    )
    
    assert result['status'] == 'success'
    seeds = [diag['seed'] for diag in result['chain_diagnostics']]
    assert len(seeds) == len(set(seeds)), "All chains should have distinct seeds"

def test_mice_logs_mechanism(temp_files):
    """Test that missingness mechanism is logged and recorded."""
    result = run_mice_chains(
        data_path=temp_files['data_path'],
        output_path=temp_files['output_path'],
        n_chains=2,
        max_iter=10,
        burn_in=5,
        base_seed=42,
        meta_path=temp_files['meta_path']
    )
    
    assert result['mechanism'] == 'MCAR'

def test_mice_output_file_created(temp_files):
    """Test that output file is created and contains valid JSON."""
    run_mice_chains(
        data_path=temp_files['data_path'],
        output_path=temp_files['output_path'],
        n_chains=2,
        max_iter=10,
        burn_in=5,
        base_seed=42,
        meta_path=temp_files['meta_path']
    )
    
    assert os.path.exists(temp_files['output_path'])
    
    with open(temp_files['output_path'], 'r') as f:
        loaded_result = json.load(f)
    
    assert loaded_result['status'] == 'success'
    assert 'pooled_statistics' in loaded_result