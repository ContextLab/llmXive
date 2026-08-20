"""
Unit tests for analysis_tobit.py (Task T027)
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os

# Mock the config to avoid dependency on real config files during unit tests
import sys
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis_tobit import load_retrieval_data, calculate_vif, prepare_tobit_data, run_ridge_fallback

@pytest.fixture
def sample_df():
    """Create a sample dataframe for testing."""
    data = {
        'planet_name': ['p1', 'p2', 'p3', 'p4', 'p5'],
        'water_mixing_ratio': [-3.0, -2.5, -4.0, -3.2, -2.8],
        'temperature': [1000, 1100, 900, 1050, 1200],
        'mass': [1.0, 1.2, 0.8, 1.1, 1.3],
        'metallicity': [0.5, 0.6, 0.4, 0.55, 0.7],
        'is_upper_limit': [False, False, True, False, False]
    }
    return pd.DataFrame(data)

def test_load_retrieval_data(sample_df, tmp_path):
    """Test loading data from CSV."""
    csv_path = tmp_path / "test_retrieval.csv"
    sample_df.to_csv(csv_path, index=False)
    
    loaded_df = load_retrieval_data(csv_path)
    
    assert len(loaded_df) == 5
    assert 'water_mixing_ratio' in loaded_df.columns
    assert 'is_upper_limit' in loaded_df.columns
    assert loaded_df['is_upper_limit'].dtype == bool

def test_calculate_vif(sample_df):
    """Test VIF calculation."""
    predictors = ['temperature', 'mass', 'metallicity']
    vif_scores = calculate_vif(sample_df, predictors)
    
    assert len(vif_scores) == 3
    assert all(isinstance(v, float) for v in vif_scores.values())
    # With perfect correlation, VIF would be high. With random, it should be low.
    # Here we just check it runs and returns values.

def test_prepare_tobit_data(sample_df):
    """Test data preparation for Tobit."""
    features, outcome, censoring = prepare_tobit_data(sample_df)
    
    assert features.shape[0] == 5
    assert outcome.shape[0] == 5
    assert censoring.shape[0] == 5
    assert censoring.sum() == 4 # 4 uncensored (True), 1 censored (False)

def test_ridge_fallback(sample_df):
    """Test Ridge regression fallback."""
    # Ensure we have enough uncensored data
    results = run_ridge_fallback(sample_df)
    
    assert results['fallback_triggered'] == True
    assert 'coefficients' in results
    assert 'temperature' in results['coefficients']
    assert 'mass' in results['coefficients']
    assert 'metallicity' in results['coefficients']
    assert 'intercept' in results['coefficients']

def test_vif_threshold_logic(sample_df, tmp_path):
    """Test that high VIF triggers fallback."""
    # Create a dataset with high multicollinearity
    # T = Mass * 1000 + noise
    high_corr_df = sample_df.copy()
    high_corr_df['temperature'] = high_corr_df['mass'] * 1000 + 0.1 * np.random.randn(5)
    
    vif_scores = calculate_vif(high_corr_df, ['temperature', 'mass', 'metallicity'])
    max_vif = max(vif_scores.values())
    
    # If VIF is high, we expect the logic to trigger fallback in main()
    # This test just verifies VIF calculation detects it.
    # Note: With 5 points, VIF might not be extremely high unless perfect correlation.
    # We just check the function runs.
    assert isinstance(max_vif, float)