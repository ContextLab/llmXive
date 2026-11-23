import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code to path for imports
current_dir = Path(__file__).parent.parent
code_dir = current_dir.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from data.split import stratified_split_by_mw, validate_split_distribution, load_processed_data
from utils.seed import set_seed

@pytest.fixture
def sample_df():
    """Creates a synthetic DataFrame mimicking the processed data structure."""
    set_seed(42)
    n = 1000
    # Generate MW with a specific distribution (normal-ish)
    mw = np.random.normal(loc=300, scale=50, size=n)
    mw = np.abs(mw) # Ensure positive
    # Generate random surface area
    sa = np.random.normal(loc=100, scale=20, size=n)
    sa = np.abs(sa)
    
    df = pd.DataFrame({
        'molecular_weight': mw,
        'surface_area': sa,
        'smiles': ['CCO' for _ in range(n)] # Dummy smiles
    })
    return df

def test_stratified_split_by_mw(sample_df):
    """Test that stratified split produces roughly equal sized sets."""
    train_idx, test_idx = stratified_split_by_mw(sample_df, test_ratio=0.2, seed=42)
    
    assert len(train_idx) + len(test_idx) == len(sample_df)
    assert len(test_idx) == int(len(sample_df) * 0.2)
    assert len(train_idx) == len(sample_df) - len(test_idx)
    
    # Check no overlap
    assert len(set(train_idx) & set(test_idx)) == 0

def test_validate_split_distribution_success(sample_df):
    """Test that a good split passes the KS test."""
    train_idx, test_idx = stratified_split_by_mw(sample_df, test_ratio=0.2, seed=42)
    p_val, is_valid = validate_split_distribution(sample_df, train_idx, test_idx)
    
    assert is_valid is True
    assert p_val > 0.05

def test_validate_split_distribution_failure():
    """Test that a bad split (e.g. by value range) fails the KS test."""
    # Create a dataset where we can easily create a bad split
    mw = np.concatenate([np.random.normal(100, 5, 500), np.random.normal(500, 5, 500)])
    df = pd.DataFrame({
        'molecular_weight': mw,
        'surface_area': np.random.normal(50, 10, 1000),
        'smiles': ['CCO'] * 1000
    })
    
    # Force a bad split: first half train, second half test
    # Since the data is bimodal and sorted, this should fail KS
    train_idx = list(range(500))
    test_idx = list(range(500, 1000))
    
    p_val, is_valid = validate_split_distribution(df, train_idx, test_idx)
    
    # This should fail because the distributions are clearly different (100 vs 500)
    assert is_valid is False
    assert p_val <= 0.05