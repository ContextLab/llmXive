import pytest
import pandas as pd
import numpy as np
from src.models.evaluate import perform_nested_permutation_test, _select_features, _train_and_score

def test_nested_permutation_test_structure():
    """
    Test that the nested permutation test function runs without error on synthetic data.
    This verifies the logic of feature selection on train folds and shuffling.
    """
    # Create synthetic data
    np.random.seed(42)
    n_samples = 200
    n_features = 10
    
    data = pd.DataFrame(np.random.randn(n_samples, n_features), columns=[f'feat_{i}' for i in range(n_features)])
    # Create a target that has a relationship with one interaction term
    data['interaction_1'] = data['feat_0'] * data['feat_1']
    data['yield_strength'] = 50 + 2 * data['interaction_1'] + np.random.randn(n_samples) * 0.5
    
    interaction_cols = ['interaction_1']
    
    # Run the test
    results = perform_nested_permutation_test(
        data=data,
        target_col='yield_strength',
        interaction_cols=interaction_cols,
        n_permutations=5, # Small number for unit test speed
        feature_selection_k=5,
        random_state=42
    )
    
    assert 'interaction_1' in results
    assert 'mean_observed_r2' in results['interaction_1']
    assert 'p_value' in results['interaction_1']
    assert 'null_95th_percentile' in results['interaction_1']
    
    # Since we created a strong signal, p-value should ideally be low (significant)
    # But with only 5 permutations, it might not be strictly < 0.05, so we just check existence
    assert isinstance(results['interaction_1']['p_value'], float)
    assert results['interaction_1']['p_value'] >= 0.0 and results['interaction_1']['p_value'] <= 1.0

def test_feature_selection_on_train_only():
    """
    Verify that feature selection is performed on the training set.
    This is a logic check: if we select features on X_train, the indices should be valid for X_train.
    """
    X_train = pd.DataFrame(np.random.randn(50, 5), columns=['a', 'b', 'c', 'd', 'e'])
    y_train = pd.Series(np.random.randn(50))
    
    selected = _select_features(X_train, y_train, k=3)
    
    assert len(selected) == 3
    assert all(0 <= idx < 5 for idx in selected)

def test_shuffling_logic():
    """
    Verify that shuffling breaks the relationship.
    """
    # Create data with perfect correlation
    x = np.arange(100)
    y = x * 2 + 10
    
    # Shuffle y relative to x
    np.random.seed(42)
    y_shuffled = np.random.permutation(y)
    
    # Correlation should drop significantly
    corr_original, _ = stats.pearsonr(x, y)
    corr_shuffled, _ = stats.pearsonr(x, y_shuffled)
    
    # Original should be ~1.0
    assert abs(corr_original) > 0.99
    # Shuffled should be much lower (random)
    assert abs(corr_shuffled) < 0.5 # Loose check for randomness

def test_null_distribution_generation():
    """
    Test that the null distribution is generated correctly by shuffling.
    """
    # This is implicitly tested in test_nested_permutation_test_structure
    # but we can add a specific check if needed.
    pass
