"""
Unit tests for the analysis module (T022).
Tests correlation computation and significance identification.
"""
import pytest
import pandas as pd
import numpy as np
from scipy import stats
import json
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analysis import (
    compute_correlation_matrix,
    compute_p_values,
    identify_significant_correlations,
    CORRELATION_THRESHOLD,
    P_VALUE_THRESHOLD
)

@pytest.fixture
def sample_data():
    """
    Creates a deterministic dataset with known correlations.
    - tpsa: Strong negative correlation with half_life (r ~ -0.7)
    - mw: Weak positive correlation (r ~ 0.2)
    - random_col: No correlation (r ~ 0.0)
    """
    np.random.seed(42)
    n = 100
    
    # Create a base variable
    x = np.random.normal(0, 1, n)
    
    # tpsa: Strong negative correlation with half_life
    # half_life = -0.7 * tpsa + noise
    tpsa = x
    half_life = -0.7 * tpsa + np.random.normal(0, 0.5, n)
    
    # mw: Weak positive correlation
    mw = 0.2 * x + np.random.normal(0, 1, n)
    # Ensure MW is positive
    mw = np.abs(mw) + 100 
    
    # other descriptors (random)
    rotatable_bonds = np.random.randint(0, 10, n)
    aromatic_rings = np.random.randint(0, 5, n)
    wiener_index = np.random.uniform(10, 100, n)
    zagreb_index = np.random.uniform(100, 1000, n)
    
    df = pd.DataFrame({
        'smiles': ['SMILES'] * n,
        'half_life_hours': half_life,
        'tpsa': tpsa,
        'rotatable_bonds': rotatable_bonds,
        'mw': mw,
        'aromatic_rings': aromatic_rings,
        'wiener_index': wiener_index,
        'zagreb_index': zagreb_index
    })
    
    return df

def test_compute_correlation_matrix(sample_data):
    """Test that correlation matrices are computed correctly."""
    pearson, spearman = compute_correlation_matrix(sample_data)
    
    # Check structure
    expected_cols = ['tpsa', 'rotatable_bonds', 'mw', 'aromatic_rings', 
                     'wiener_index', 'zagreb_index', 'half_life_hours']
    assert list(pearson.columns) == expected_cols
    assert list(spearman.columns) == expected_cols
    
    # Check diagonal is 1.0
    for col in expected_cols:
        assert abs(pearson.loc[col, col] - 1.0) < 1e-6
        assert abs(spearman.loc[col, col] - 1.0) < 1e-6

def test_compute_p_values(sample_data):
    """Test p-value computation matches scipy.stats.pearsonr."""
    results = compute_p_values(sample_data)
    
    # Verify against scipy directly for 'tpsa'
    corr_scipy, p_scipy = stats.pearsonr(sample_data['tpsa'], sample_data['half_life_hours'])
    
    assert abs(results['tpsa']['correlation'] - corr_scipy) < 1e-6
    assert abs(results['tpsa']['p_value'] - p_scipy) < 1e-6

def test_identify_significant_correlations(sample_data):
    """
    Test identification of significant correlations based on thresholds.
    Expected: tpsa should be significant (r ~ -0.7, p < 0.05).
    mw should likely NOT be significant (r ~ 0.2).
    """
    p_values = compute_p_values(sample_data)
    significant = identify_significant_correlations(p_values)
    
    significant_descriptors = [item['descriptor'] for item in significant]
    
    # tpsa must be significant
    assert 'tpsa' in significant_descriptors, "tpsa should be significant given the synthetic data"
    
    # Check structure of significant items
    for item in significant:
        assert 'descriptor' in item
        assert 'correlation' in item
        assert 'p_value' in item
        assert abs(item['correlation']) >= CORRELATION_THRESHOLD
        assert item['p_value'] < P_VALUE_THRESHOLD

def test_correlation_threshold_boundary():
    """Test logic at exact threshold boundary."""
    # Create data with r = 0.5 exactly
    n = 50
    x = np.linspace(0, 1, n)
    y = 0.5 * x + np.random.normal(0, 0.01, n) # Very low noise to keep r ~ 0.5
    
    # Force exact r=0.5 if possible, but due to noise it will be close.
    # Instead, test the filtering logic directly with a mock result dict.
    
    mock_results = {
        'feature_a': {'correlation': 0.5, 'p_value': 0.04}, # Should pass
        'feature_b': {'correlation': 0.49, 'p_value': 0.04}, # Should fail (r < 0.5)
        'feature_c': {'correlation': 0.5, 'p_value': 0.06}, # Should fail (p > 0.05)
        'feature_d': {'correlation': 0.6, 'p_value': 0.01}  # Should pass
    }
    
    significant = identify_significant_correlations(mock_results)
    sig_names = [s['descriptor'] for s in significant]
    
    assert 'feature_a' in sig_names
    assert 'feature_d' in sig_names
    assert 'feature_b' not in sig_names
    assert 'feature_c' not in sig_names