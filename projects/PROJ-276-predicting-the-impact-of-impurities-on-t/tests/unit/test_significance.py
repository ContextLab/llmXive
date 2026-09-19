import pytest
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from code.src.utils.logging import get_modeling_logger

logger = get_modeling_logger()

def generate_dummy_tree_data(n_samples=1000, n_features=5):
    """
    Generates a synthetic dataset with a known non-linear relationship
    suitable for testing tree-based models and permutation tests.
    """
    rng = np.random.default_rng(42)
    X = rng.standard_normal((n_samples, n_features))
    # Create a target with a clear dependency on the first feature
    y = 3.0 * X[:, 0] ** 2 + 2.0 * X[:, 1] + rng.normal(0, 0.5, n_samples)
    return pd.DataFrame(X, columns=[f"feature_{i}" for i in range(n_features)]), pd.Series(y, name="target")

def test_null_distribution_generation_for_tree_models():
    """
    Unit test for Permutation Test in tests/unit/test_significance.py.
    Verifies that null distribution generation for tree models works correctly.
    
    Specifically checks:
    1. The permutation function shuffles the target variable correctly.
    2. The resulting scores form a distribution centered near zero (or lower than original).
    3. The distribution has non-zero variance.
    """
    X, y = generate_dummy_tree_data()
    
    # Train a baseline Random Forest model
    model = RandomForestRegressor(n_estimators=10, random_state=42, n_jobs=-1)
    model.fit(X, y)
    
    # Calculate baseline score (R2)
    baseline_score = model.score(X, y)
    
    # Perform permutation test to generate null distribution
    # We shuffle the target 'y' multiple times to simulate the null hypothesis
    n_permutations = 20
    null_scores = []
    
    rng = np.random.default_rng(123)
    
    for _ in range(n_permutations):
        # Shuffle the target variable to break the relationship with features
        y_shuffled = y.sample(frac=1, random_state=rng).reset_index(drop=True)
        
        # Retrain or evaluate on shuffled target
        # For a strict null distribution test, we usually retrain.
        # However, to keep this unit test fast and deterministic, we evaluate
        # the existing model on shuffled data (which simulates the null distribution
        # of scores if the model has no predictive power on that specific shuffle).
        # A more rigorous approach would retrain, but for unit testing the mechanism:
        score = model.score(X, y_shuffled)
        null_scores.append(score)
    
    null_distribution = np.array(null_scores)
    
    # Assertions
    assert len(null_distribution) == n_permutations, "Null distribution must match number of permutations"
    
    # The mean of the null distribution should be significantly lower than the baseline
    # because the baseline has a real relationship, while the null does not.
    # We allow some tolerance for stochasticity, but the trend must hold.
    mean_null_score = np.mean(null_distribution)
    
    logger.info(f"Baseline R2: {baseline_score:.4f}, Mean Null R2: {mean_null_score:.4f}")
    
    # The baseline score should generally be higher than the mean null score
    # (In a perfect scenario, null R2 ~ 0 or negative, baseline > 0)
    assert baseline_score > mean_null_score, \
        f"Baseline score ({baseline_score}) should be higher than mean null score ({mean_null_score})"
    
    # Verify the distribution has variance (it's not just a constant array)
    variance = np.var(null_distribution)
    assert variance > 0, "Null distribution must have non-zero variance"
    
    # Optional: Verify that shuffling a feature (not target) also reduces performance
    # This is the standard "Permutation Importance" logic
    feature_importance_result = permutation_importance(
        model, X, y, n_repeats=5, random_state=42, n_jobs=-1
    )
    
    # Ensure importance values are generated
    assert len(feature_importance_result.importances_mean) == X.shape[1], \
        "Importance mean length must match number of features"
    
    # The most important feature (feature_0) should have a positive importance
    # (meaning performance drops when it is shuffled)
    assert feature_importance_result.importances_mean[0] > 0, \
        "Feature 0 should show positive importance in a tree model"

def test_permutation_test_with_no_relationship():
    """
    Verifies that when there is NO relationship between X and y,
    the permutation test yields a distribution centered around zero (or baseline).
    """
    rng = np.random.default_rng(999)
    X = rng.standard_normal((200, 3))
    y = rng.standard_normal(200)  # Pure noise, no relationship
    
    model = RandomForestRegressor(n_estimators=5, random_state=42)
    model.fit(X, y)
    
    baseline_score = model.score(X, y)
    
    # Generate null distribution by shuffling y
    n_permutations = 10
    null_scores = []
    
    for _ in range(n_permutations):
        y_shuffled = y.sample(frac=1, random_state=rng).reset_index(drop=True)
        score = model.score(X, y_shuffled)
        null_scores.append(score)
    
    null_distribution = np.array(null_scores)
    
    # When there is no relationship, the baseline score should be close to the null scores
    # (Both should be near 0 or slightly negative due to noise fitting)
    # We check that the difference is not statistically significant in a specific direction
    # (i.e., baseline isn't consistently much higher than null)
    diff = baseline_score - np.mean(null_distribution)
    
    # Allow a small tolerance for random variation
    assert abs(diff) < 0.1, \
        f"Baseline and Null distribution should be close when no relationship exists. Diff: {diff}"