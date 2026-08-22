"""
Unit tests for regime analysis and local feature importance.
"""
import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

from code.analysis.regimes import identify_regimes, analyze_regimes
from code.analysis.feature_importance import get_top_features, aggregate_importance

@pytest.fixture
def sample_data():
    """Create a sample dataset for testing."""
    np.random.seed(42)
    n = 100
    delta_k = np.linspace(1, 20, n)
    # Simulate Paris law with some noise
    da_dN = 1e-10 * (delta_k ** 3) * np.exp(np.random.normal(0, 0.2, n))
    
    # Add some composition features
    composition_A = np.random.uniform(0.1, 5.0, n)
    composition_B = np.random.uniform(0.1, 3.0, n)
    heat_treatment = np.random.choice(["Annealed", "Quenched", "Tempered"], n)
    
    df = pd.DataFrame({
        'delta_k': delta_k,
        'da_dN': da_dN,
        'comp_A': composition_A,
        'comp_B': composition_B,
        'heat_treatment': heat_treatment
    })
    return df

@pytest.fixture
def trained_rf_model(sample_data):
    """Train a simple RF model for testing."""
    feature_cols = ['comp_A', 'comp_B']
    X = sample_data[feature_cols]
    y = np.log(sample_data['da_dN'])
    
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X, y)
    return model, feature_cols

def test_identify_regimes_ruptures_fallback(sample_data):
    """Test regime identification with fallback method."""
    result = identify_regimes(sample_data, 'delta_k', 'da_dN')
    
    assert 'method' in result
    assert 'boundaries' in result
    assert 'regime_count' in result
    assert result['regime_count'] >= 1
    assert isinstance(result['boundaries'], list)

def test_analyze_regimes_returns_structure(sample_data, trained_rf_model):
    """Test that analyze_regimes returns expected structure."""
    model, feature_cols = trained_rf_model
    result = analyze_regimes(sample_data, model, feature_cols)
    
    assert 'method' in result
    assert 'regimes' in result
    assert 'total_regimes' in result
    assert len(result['regimes']) >= 1
    
    for regime in result['regimes']:
        assert 'name' in regime
        assert 'r2' in regime
        assert 'delta_k_range' in regime
        assert 'feature_importance' in regime

def test_local_r2_calculation(sample_data, trained_rf_model):
    """Test that local R^2 is calculated correctly."""
    model, feature_cols = trained_rf_model
    result = analyze_regimes(sample_data, model, feature_cols)
    
    for regime in result['regimes']:
        if regime['n_samples'] >= 5:
            # R^2 should be a float
            assert isinstance(regime['r2'], float)
            # R^2 can be negative but should be finite
            assert np.isfinite(regime['r2'])

def test_feature_importance_extraction(sample_data, trained_rf_model):
    """Test that feature importance is extracted correctly."""
    model, feature_cols = trained_rf_model
    result = analyze_regimes(sample_data, model, feature_cols)
    
    for regime in result['regimes']:
        if regime['n_samples'] >= 5:
            importance = regime['feature_importance']
            if importance is not None:
                assert 'raw' in importance
                assert 'top_features' in importance
                assert isinstance(importance['top_features'], list)
                # Should have at most 3 top features
                assert len(importance['top_features']) <= 3
                # Each top feature should be a tuple (name, score)
                for feat in importance['top_features']:
                    assert isinstance(feat, tuple)
                    assert len(feat) == 2

def test_get_top_features_excludes_delta_k():
    """Test that Delta K is excluded from top features."""
    importance_dict = {
        'delta_k': 0.5,
        'comp_A': 0.3,
        'comp_B': 0.2
    }
    
    top_features = get_top_features(importance_dict, exclude=['delta_k'], top_n=3)
    
    # Delta K should not be in the top features
    feature_names = [f[0] for f in top_features]
    assert 'delta_k' not in feature_names
    assert len(top_features) == 2

def test_aggregate_importance():
    """Test importance aggregation across multiple models."""
    dicts = [
        {'comp_A': 0.3, 'comp_B': 0.2, 'delta_k': 0.5},
        {'comp_A': 0.4, 'comp_B': 0.1, 'delta_k': 0.5},
        {'comp_A': 0.35, 'comp_B': 0.25, 'delta_k': 0.5}
    ]
    
    aggregated = aggregate_importance(dicts)
    
    assert 'comp_A' in aggregated
    assert 'comp_B' in aggregated
    assert 'delta_k' in aggregated
    # Check mean calculation
    assert np.isclose(aggregated['comp_A'], (0.3 + 0.4 + 0.35) / 3)

def test_analyze_regimes_small_sample_handling(sample_data, trained_rf_model):
    """Test handling of regimes with too few samples."""
    model, feature_cols = trained_rf_model
    
    # Create data with very small regimes
    small_data = sample_data.head(5)
    result = analyze_regimes(small_data, model, feature_cols)
    
    # Should still return a result, possibly with fewer regimes
    assert 'regimes' in result
    # All returned regimes should have sufficient samples
    for regime in result['regimes']:
        assert regime['n_samples'] >= 5

def test_analyze_regimes_with_linear_model(sample_data):
    """Test regime analysis with a linear model."""
    np.random.seed(42)
    df = sample_data.copy()
    df['log_da_dN'] = np.log(df['da_dN'])
    
    feature_cols = ['comp_A', 'comp_B']
    X = df[feature_cols]
    y = df['log_da_dN']
    
    model = LinearRegression()
    model.fit(X, y)
    
    result = analyze_regimes(df, model, feature_cols)
    
    assert 'regimes' in result
    assert len(result['regimes']) >= 1
    for regime in result['regimes']:
        if regime['n_samples'] >= 5:
            assert np.isfinite(regime['r2'])
            if regime['feature_importance'] is not None:
                assert 'top_features' in regime['feature_importance']
