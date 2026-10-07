import pytest
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score
from pathlib import Path
import tempfile
import joblib
from sklearn.linear_model import Lasso

# Import the function to test
# Note: We are testing the logic, not the full pipeline which requires real data
# We will mock the necessary components
from code.permutation_test import run_permutation_test

def test_permutation_test_logic():
    """
    Test that the permutation test correctly calculates p-values.
    We create a simple scenario where we know the expected outcome.
    """
    # Create simple synthetic data for testing the logic (NOT for production)
    # This is a unit test, so synthetic data is acceptable here to verify logic
    np.random.seed(42)
    n_samples = 100
    X = np.random.randn(n_samples, 5)
    y = X[:, 0] + np.random.randn(n_samples) * 0.1  # Strong signal in first feature
    
    # Train a simple model
    model = Lasso(alpha=0.1)
    model.fit(X, y)
    
    # Save and load model to simulate real usage
    with tempfile.NamedTemporaryFile(suffix='.joblib', delete=False) as f:
        model_path = Path(f.name)
        joblib.dump(model, model_path)
    
    try:
        # Run permutation test
        result = run_permutation_test(
            model_path=model_path,
            X_train=X,
            y_train=y,
            X_test=X,
            y_test=y,
            metric_func=r2_score,
            n_iterations=100,  # Small number for speed
            random_seed=42,
            condition_name="test",
            model_type="Lasso"
        )
        
        # Verify structure
        assert "p_value" in result
        assert "true_score" in result
        assert "null_mean" in result
        assert result["n_iterations"] == 100
        
        # With a strong signal, the true score should be high (close to 1)
        # The p-value should be low (significantly better than random)
        # Note: With only 100 iterations, p-value might not be extremely low, 
        # but it should be < 0.5 for a good model
        assert result["true_score"] > 0.5, "True score should be high for this synthetic data"
        assert result["p_value"] < 0.5, "P-value should be low for a good model"
        
        print(f"Test passed: true_score={result['true_score']:.4f}, p_value={result['p_value']:.4f}")
        
    finally:
        model_path.unlink()

def test_permutation_test_random_model():
    """
    Test that a model with no predictive power yields a high p-value.
    """
    np.random.seed(42)
    n_samples = 100
    X = np.random.randn(n_samples, 5)
    y = np.random.randn(n_samples)  # No relationship between X and y
    
    model = Lasso(alpha=0.1)
    model.fit(X, y)
    
    with tempfile.NamedTemporaryFile(suffix='.joblib', delete=False) as f:
        model_path = Path(f.name)
        joblib.dump(model, model_path)
    
    try:
        result = run_permutation_test(
            model_path=model_path,
            X_train=X,
            y_train=y,
            X_test=X,
            y_test=y,
            metric_func=r2_score,
            n_iterations=100,
            random_seed=42,
            condition_name="test",
            model_type="Lasso"
        )
        
        # With no signal, the true score should be close to 0 (or negative)
        # The p-value should be around 0.5 (random)
        assert result["p_value"] > 0.2, "P-value should be high for a random model"
        
        print(f"Test passed: true_score={result['true_score']:.4f}, p_value={result['p_value']:.4f}")
        
    finally:
        model_path.unlink()
