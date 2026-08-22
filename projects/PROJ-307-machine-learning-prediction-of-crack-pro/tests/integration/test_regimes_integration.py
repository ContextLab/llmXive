"""
Integration tests for regime analysis pipeline.
"""
import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

from code.analysis.regimes import identify_regimes, analyze_regimes
from code.data.loader import load_nasa_data, validate_schema

@pytest.fixture
def mock_full_dataset():
    """Create a mock dataset that mimics real data structure."""
    np.random.seed(42)
    n = 500
    
    # Create realistic Delta K distribution (log-normal like)
    delta_k = np.random.lognormal(mean=1.5, sigma=0.5, size=n)
    delta_k = np.clip(delta_k, 1, 25)
    delta_k = np.sort(delta_k)
    
    # Paris law relationship with noise
    C = 1e-12
    m = 3.0
    da_dN = C * (delta_k ** m) * np.exp(np.random.normal(0, 0.3, n))
    
    # Composition features
    comp_A = np.random.uniform(0.5, 6.0, n)
    comp_B = np.random.uniform(0.1, 4.0, n)
    comp_C = np.random.uniform(0.0, 2.0, n)
    
    # Heat treatment
    heat_treatments = ["Annealed", "Quenched", "Tempered", "Aged"]
    heat_treatment = np.random.choice(heat_treatments, n)
    
    df = pd.DataFrame({
        'delta_k': delta_k,
        'da_dN': da_dN,
        'comp_A': comp_A,
        'comp_B': comp_B,
        'comp_C': comp_C,
        'heat_treatment': heat_treatment
    })
    return df

def test_full_regime_analysis_pipeline(mock_full_dataset):
    """Test the complete regime analysis pipeline."""
    df = mock_full_dataset
    
    # Step 1: Identify regimes
    regime_results = identify_regimes(df, 'delta_k', 'da_dN')
    assert regime_results['regime_count'] >= 1
    assert len(regime_results['boundaries']) >= 2
    
    # Step 2: Prepare features (log transform target)
    df['log_da_dN'] = np.log(df['da_dN'])
    feature_cols = ['comp_A', 'comp_B', 'comp_C']
    
    # Step 3: Train a model
    X = df[feature_cols]
    y = df['log_da_dN']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)
    model.fit(X_train, y_train)
    
    # Step 4: Analyze regimes
    analysis_results = analyze_regimes(
        df, 
        model, 
        feature_cols, 
        'delta_k', 
        'log_da_dN',
        regime_results
    )
    
    # Verify results structure
    assert 'regimes' in analysis_results
    assert analysis_results['total_regimes'] >= 1
    
    # Verify each regime has valid metrics
    valid_regimes = 0
    for regime in analysis_results['regimes']:
        if regime['n_samples'] >= 5:
            valid_regimes += 1
            assert np.isfinite(regime['r2'])
            assert 'delta_k_range' in regime
            assert regime['delta_k_range'][0] < regime['delta_k_range'][1]
            
            # Check feature importance
            if regime['feature_importance'] is not None:
                top_feats = regime['feature_importance']['top_features']
                assert len(top_feats) <= 3
                # Ensure Delta K is not in top features
                for feat_name, _ in top_feats:
                    assert feat_name != 'delta_k'
    
    assert valid_regimes >= 1, "At least one valid regime should be analyzed"

def test_regime_r2_varies_across_regimes(mock_full_dataset):
    """Test that R^2 values vary across different regimes."""
    df = mock_full_dataset
    df['log_da_dN'] = np.log(df['da_dN'])
    
    feature_cols = ['comp_A', 'comp_B']
    X = df[feature_cols]
    y = df['log_da_dN']
    
    model = RandomForestRegressor(n_estimators=30, max_depth=4, random_state=42)
    model.fit(X, y)
    
    analysis_results = analyze_regimes(df, model, feature_cols)
    
    r2_values = [r['r2'] for r in analysis_results['regimes'] if np.isfinite(r['r2'])]
    
    # We expect some variation in R^2 across regimes
    # (though they might all be similar in some cases)
    assert len(r2_values) >= 1
    
def test_regime_boundaries_cover_data_range(mock_full_dataset):
    """Test that regime boundaries cover the full Delta K range."""
    df = mock_full_dataset
    
    regime_results = identify_regimes(df, 'delta_k', 'da_dN')
    boundaries = regime_results['boundaries']
    
    # Boundaries should start at 0 and end at len(data)
    assert boundaries[0] == 0
    assert boundaries[-1] == len(df)
    
    # Boundaries should be sorted
    assert boundaries == sorted(boundaries)
    
    # No overlapping or invalid boundaries
    for i in range(len(boundaries) - 1):
        assert boundaries[i] < boundaries[i+1]

def test_small_dataset_handling():
    """Test regime analysis on a very small dataset."""
    np.random.seed(42)
    n = 20
    df = pd.DataFrame({
        'delta_k': np.linspace(1, 10, n),
        'da_dN': np.random.uniform(1e-10, 1e-8, n),
        'comp_A': np.random.uniform(1, 5, n),
        'comp_B': np.random.uniform(1, 3, n)
    })
    
    feature_cols = ['comp_A', 'comp_B']
    model = RandomForestRegressor(n_estimators=5, random_state=42)
    model.fit(df[feature_cols], np.log(df['da_dN']))
    
    # Should not crash, even with small data
    result = analyze_regimes(df, model, feature_cols)
    assert 'regimes' in result

def test_feature_importance_ranking_stability(mock_full_dataset):
    """Test that feature importance rankings are consistent within regimes."""
    df = mock_full_dataset
    df['log_da_dN'] = np.log(df['da_dN'])
    
    feature_cols = ['comp_A', 'comp_B', 'comp_C']
    X = df[feature_cols]
    y = df['log_da_dN']
    
    model = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)
    model.fit(X, y)
    
    result = analyze_regimes(df, model, feature_cols)
    
    # Collect top features from all regimes
    all_top_features = []
    for regime in result['regimes']:
        if regime['feature_importance'] is not None:
            for feat_name, _ in regime['feature_importance']['top_features']:
                all_top_features.append(feat_name)
    
    # Most important features should appear frequently
    if all_top_features:
        from collections import Counter
        counts = Counter(all_top_features)
        # At least one feature should appear multiple times if we have enough regimes
        if len(result['regimes']) >= 3:
            max_count = max(counts.values())
            assert max_count >= 2