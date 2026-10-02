"""
Unit tests for the training script logic.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import functions to test
from code.src.modeling.train import (
    load_clean_data, 
    prepare_features_targets, 
    train_model,
    TimeoutGuard,
    TimeoutError
)

@pytest.fixture
def sample_data():
    """Create a synthetic but realistic dataset for testing."""
    np.random.seed(42)
    n = 100
    data = {
        'Tc': np.random.uniform(20, 40, n),
        'impurity_Al_pct': np.random.uniform(0, 5, n),
        'impurity_C_pct': np.random.uniform(0, 5, n),
        'impurity_Si_pct': np.random.uniform(0, 2, n),
        'pressure_GPa': np.random.uniform(0, 1, n),
        'impurity_category': np.random.choice(['Al', 'C', 'Si', 'None'], n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv(sample_data):
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        sample_data.to_csv(f, index=False)
        return f.name

def test_load_clean_data_success(temp_csv):
    df = load_clean_data(temp_csv)
    assert not df.empty
    assert 'Tc' in df.columns

def test_load_clean_data_missing_file():
    with pytest.raises(SystemExit):
        load_clean_data("non_existent_file.csv")

def test_load_clean_data_empty_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("col1,col2\n") # Header only
        f.flush()
        with pytest.raises(SystemExit):
            load_clean_data(f.name)
    os.unlink(f.name)

def test_prepare_features_targets(sample_data):
    X, y, y_strat = prepare_features_targets(sample_data)
    
    assert isinstance(X, pd.DataFrame)
    assert isinstance(y, pd.Series)
    assert isinstance(y_strat, pd.Series)
    
    assert 'Tc' not in X.columns
    assert 'impurity_category' not in X.columns
    assert len(X) == len(sample_data)
    assert len(y) == len(sample_data)

def test_prepare_features_targets_missing_stratification(sample_data):
    # Remove stratification column
    df_no_strat = sample_data.drop(columns=['impurity_category'])
    X, y, y_strat = prepare_features_targets(df_no_strat)
    
    # Should fallback to binning Tc
    assert y_strat.name == 'temp_bin' or y_strat.name == 'Tc'
    assert len(X) == len(df_no_strat)

def test_timeout_guard():
    """Test that the timeout guard raises TimeoutError."""
    with pytest.raises(TimeoutError):
        with TimeoutGuard(0.1):
            time.sleep(0.5) # Sleep longer than timeout

def test_timeout_guard_success():
    """Test that the timeout guard allows short tasks."""
    import time
    start = time.time()
    with TimeoutGuard(2):
        time.sleep(0.1)
    end = time.time()
    assert (end - start) < 1.0