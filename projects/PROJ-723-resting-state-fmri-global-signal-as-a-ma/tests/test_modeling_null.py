import pytest
import numpy as np
import json
import os
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, GridSearchCV
from sklearn.metrics import mean_absolute_error

# Import functions to test
from modeling import calculate_empirical_p_value, run_null_distribution_pipeline

def test_calculate_empirical_p_value():
    """Test the p-value calculation formula."""
    # Scenario: Observed MAE is lower than all null MAEs (strong effect)
    # Null: [5, 6, 7, 8, 9], Observed: 4
    # Count <= 4 is 0. N=5. p = (0+1)/(5+1) = 1/6
    null_samples = [5.0, 6.0, 7.0, 8.0, 9.0]
    observed = 4.0
    p = calculate_empirical_p_value(observed, null_samples)
    assert abs(p - 1.0/6.0) < 1e-6

    # Scenario: Observed MAE is higher than all null MAEs (no effect)
    # Null: [1, 2, 3], Observed: 10
    # Count <= 10 is 3. N=3. p = (3+1)/(3+1) = 1.0
    null_samples_2 = [1.0, 2.0, 3.0]
    observed_2 = 10.0
    p_2 = calculate_empirical_p_value(observed_2, null_samples_2)
    assert abs(p_2 - 1.0) < 1e-6

def test_null_distribution_pipeline_structure():
    """Test that the null distribution pipeline runs and returns expected keys."""
    # Create small synthetic data for testing logic (not for final results)
    np.random.seed(42)
    X = np.random.rand(50, 5)
    y = np.random.rand(50)
    
    # Run with small N to save time in test
    result = run_null_distribution_pipeline(X, y, n_permutations=10, n_splits=3, seed=42)
    
    assert 'null_mae_samples' in result
    assert 'null_r2_samples' in result
    assert len(result['null_mae_samples']) == 10
    assert len(result['null_r2_samples']) == 10
    assert 'n_permutations' in result
    assert result['n_permutations'] == 10