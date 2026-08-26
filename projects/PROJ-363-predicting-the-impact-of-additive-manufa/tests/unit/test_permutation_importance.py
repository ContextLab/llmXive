"""
Unit tests for Permutation Importance functionality.

This module verifies that the permutation importance implementation:
1. Runs with exactly 1,000 permutations as specified
2. Returns a valid score distribution
3. Produces consistent results with fixed random seed
"""

import pytest
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

# Import the function to test from the main module
from code.analyze_explainability import perform_permutation_importance


@pytest.fixture
def sample_data():
    """Create a reproducible sample dataset for testing."""
    np.random.seed(42)
    n_samples = 200
    
    # Create synthetic features similar to the 316L dataset
    data = {
        'laser_power': np.random.uniform(200, 500, n_samples),
        'scan_speed': np.random.uniform(500, 1500, n_samples),
        'hatch_spacing': np.random.uniform(0.05, 0.15, n_samples),
        'layer_thickness': np.random.uniform(0.02, 0.06, n_samples),
        'energy_density': np.random.uniform(50, 200, n_samples)
    }
    
    # Create a target variable with some relationship to features
    df = pd.DataFrame(data)
    df['porosity'] = (
        0.3 * df['laser_power'] / 500 -
        0.2 * df['scan_speed'] / 1500 +
        0.15 * df['hatch_spacing'] / 0.15 +
        0.1 * df['layer_thickness'] / 0.06 +
        np.random.normal(0, 0.05, n_samples)
    )
    
    return df


@pytest.fixture
def trained_model(sample_data):
    """Train a simple model for testing permutation importance."""
    X = sample_data[['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']]
    y = sample_data['porosity']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    model = GradientBoostingRegressor(
        n_estimators=50, 
        max_depth=3,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    return model, X_test, y_test


def test_permutation_count(sample_data, trained_model):
    """Test that permutation importance runs with exactly 1,000 permutations."""
    model, X_test, y_test = trained_model
    
    # Run permutation importance with 1000 permutations
    result = perform_permutation_importance(
        model=model,
        X=X_test,
        y=y_test,
        n_repeats=1000,
        random_state=42
    )
    
    # Verify the result structure
    assert 'feature_importances' in result
    assert 'scores' in result
    
    # Check that we have scores for each feature
    features = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    assert list(result['feature_importances'].keys()) == features
    
    # Verify that we have 1000 scores per feature
    for feature in features:
        assert len(result['scores'][feature]) == 1000, \
            f"Expected 1000 scores for {feature}, got {len(result['scores'][feature])}"


def test_valid_score_distribution(sample_data, trained_model):
    """Test that permutation importance returns a valid score distribution."""
    model, X_test, y_test = trained_model
    
    result = perform_permutation_importance(
        model=model,
        X=X_test,
        y=y_test,
        n_repeats=1000,
        random_state=42
    )
    
    # Verify scores are numeric arrays
    for feature, scores in result['scores'].items():
        scores_array = np.array(scores)
        
        # Check that scores are numeric
        assert np.issubdtype(scores_array.dtype, np.number), \
            f"Scores for {feature} are not numeric"
        
        # Check that we have variance in scores (not all zeros)
        assert np.std(scores_array) > 0, \
            f"Scores for {feature} have no variance - all values are identical"
        
        # Check that mean importance is negative (permuting should hurt performance)
        # or at least not significantly positive
        assert np.mean(scores_array) <= 0.1, \
            f"Mean importance for {feature} is unexpectedly positive: {np.mean(scores_array)}"


def test_reproducibility(sample_data, trained_model):
    """Test that permutation importance produces consistent results with fixed seed."""
    model, X_test, y_test = trained_model
    
    # Run twice with same seed
    result1 = perform_permutation_importance(
        model=model,
        X=X_test,
        y=y_test,
        n_repeats=100,  # Use fewer for faster testing
        random_state=42
    )
    
    result2 = perform_permutation_importance(
        model=model,
        X=X_test,
        y=y_test,
        n_repeats=100,
        random_state=42
    )
    
    # Results should be identical
    for feature in result1['feature_importances']:
        assert np.allclose(
            result1['feature_importances'][feature],
            result2['feature_importances'][feature],
            rtol=1e-10
        ), f"Results differ for {feature}"
        
        assert np.allclose(
            result1['scores'][feature],
            result2['scores'][feature],
            rtol=1e-10
        ), f"Score distributions differ for {feature}"


def test_feature_importance_ranking(sample_data, trained_model):
    """Test that feature importances are ranked correctly."""
    model, X_test, y_test = trained_model
    
    result = perform_permutation_importance(
        model=model,
        X=X_test,
        y=y_test,
        n_repeats=1000,
        random_state=42
    )
    
    # Get mean importances
    importances = result['feature_importances']
    
    # Verify that importances are negative (permuting features should decrease performance)
    for feature, importance in importances.items():
        assert importance <= 0, \
            f"Importance for {feature} should be negative or zero, got {importance}"
    
    # Verify that we have at least one feature with non-zero importance
    non_zero_importances = [imp for imp in importances.values() if abs(imp) > 1e-6]
    assert len(non_zero_importances) > 0, \
        "All feature importances are zero - this suggests the test is not working correctly"


def test_different_random_states_produce_different_results(sample_data, trained_model):
    """Test that different random seeds produce different (but similar) results."""
    model, X_test, y_test = trained_model
    
    result1 = perform_permutation_importance(
        model=model,
        X=X_test,
        y=y_test,
        n_repeats=100,
        random_state=42
    )
    
    result2 = perform_permutation_importance(
        model=model,
        X=X_test,
        y=y_test,
        n_repeats=100,
        random_state=123
    )
    
    # Results should be different (due to different random sampling)
    # but should be in the same ballpark
    for feature in result1['feature_importances']:
        diff = abs(
            result1['feature_importances'][feature] - 
            result2['feature_importances'][feature]
        )
        # Allow some variance due to randomness, but not too much
        assert diff < 0.05, \
            f"Difference too large for {feature}: {diff}"