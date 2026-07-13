"""
Unit tests for collinearity diagnostics.

Tests VIF calculation, collinearity flagging, and descriptive language generation.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from diagnostics.collinearity import (
    prepare_design_matrix,
    calculate_vif,
    flag_collinearity,
    flag_collinearity,
    analyze_collinearity,
    VIF_THRESHOLD
)

@pytest.fixture
def sample_data_with_collinearity():
    """Create sample data with known collinearity."""
    n = 100
    np.random.seed(42)
    
    # Create highly correlated features
    x1 = np.random.normal(0, 1, n)
    x2 = x1 * 0.95 + np.random.normal(0, 0.1, n)  # Highly correlated with x1
    x3 = np.random.normal(0, 1, n)  # Independent
    
    df = pd.DataFrame({
        'feature1': x1,
        'feature2': x2,
        'feature3': x3,
        'target': np.random.normal(0, 1, n)
    })
    
    return df

@pytest.fixture
def sample_data_no_collinearity():
    """Create sample data with no collinearity."""
    n = 100
    np.random.seed(42)
    
    # Create independent features
    df = pd.DataFrame({
        'feature1': np.random.normal(0, 1, n),
        'feature2': np.random.normal(0, 1, n),
        'feature3': np.random.normal(0, 1, n),
        'target': np.random.normal(0, 1, n)
    })
    
    return df

def test_prepare_design_matrix(sample_data_with_collinearity):
    """Test that design matrix is prepared correctly."""
    X, features = prepare_design_matrix(sample_data_with_collinearity)
    
    assert 'const' in X.columns
    assert 'feature1' in X.columns
    assert 'feature2' in X.columns
    assert 'feature3' in X.columns
    assert 'target' not in X.columns
    assert len(X) == len(sample_data_with_collinearity)

def test_calculate_vif_returns_positive_values(sample_data_with_collinearity):
    """Test that VIF values are positive."""
    X, features = prepare_design_matrix(sample_data_with_collinearity)
    vif_results = calculate_vif(X, features)
    
    assert len(vif_results) == len(features)
    assert all(vif_results['vif'] > 0)

def test_flag_collinearity_identifies_high_vif(sample_data_with_collinearity):
    """Test that flag_collinearity correctly identifies high VIF features."""
    X, features = prepare_design_matrix(sample_data_with_collinearity)
    vif_results = calculate_vif(X, features)
    flags = flag_collinearity(vif_results)
    
    # At least one feature should be flagged due to high correlation
    assert flags['count_flagged'] >= 1
    assert 'descriptive_language' in flags
    assert 'joint relationship' in flags['descriptive_language'].lower() or \
           'correlated' in flags['descriptive_language'].lower()

def test_flag_collinearity_no_high_vif(sample_data_no_collinearity):
    """Test flag_collinearity when no features have high VIF."""
    X, features = prepare_design_matrix(sample_data_no_collinearity)
    vif_results = calculate_vif(X, features)
    flags = flag_collinearity(vif_results)
    
    # With independent features, likely no flags (or very few)
    assert 'descriptive_language' in flags
    # Should mention no significant collinearity
    assert 'not a significant concern' in flags['descriptive_language'] or \
           'threshold' in flags['descriptive_language'].lower()

def test_descriptive_language_format(sample_data_with_collinearity):
    """Test that descriptive language follows FR-006 requirements."""
    X, features = prepare_design_matrix(sample_data_with_collinearity)
    vif_results = calculate_vif(X, features)
    flags = flag_collinearity(vif_results)
    
    desc = flags['descriptive_language']
    
    # Should mention joint relationship or correlated predictors
    assert 'joint relationship' in desc.lower() or \
           'correlated' in desc.lower() or \
           'multicollinearity' in desc.lower()
    
    # Should warn against independent effects interpretation
    assert 'independent' in desc.lower() or \
           'individual' in desc.lower()

def test_analyze_collinearity_structure(sample_data_with_collinearity):
    """Test that analyze_collinearity returns expected structure."""
    results = analyze_collinearity(sample_data_with_collinearity)
    
    assert 'vif_table' in results
    assert 'collinearity_flags' in results
    assert 'design_matrix_shape' in results
    assert 'n_observations' in results
    assert 'n_predictors' in results
    
    # Check collinearity_flags structure
    flags = results['collinearity_flags']
    assert 'high_collinearity_features' in flags
    assert 'low_collinearity_features' in flags
    assert 'descriptive_language' in flags
    assert 'interpretation' in flags
    assert 'threshold' in flags