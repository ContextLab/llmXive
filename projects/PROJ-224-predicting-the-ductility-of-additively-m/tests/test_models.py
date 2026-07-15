"""
Unit tests for the mixed-effects model implementation.
"""

import pytest
import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor
import warnings
from sklearn.model_selection import train_test_split
import os
import sys
import tempfile
import json
from pathlib import Path

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.lme_model import fit_lme_model, extract_results, prepare_features
from models.save_lme_artifact import save_lme_artifact

@pytest.fixture
def sample_lme_data():
    """Generate a small synthetic dataset for testing LME convergence."""
    np.random.seed(42)
    n = 100
    n_groups = 5
    
    # Create groups
    groups = np.repeat([f"Alloy_{i}" for i in range(n_groups)], n // n_groups)
    
    # Create fixed effects
    X = pd.DataFrame({
        'energy_density': np.random.uniform(50, 150, n),
        'laser_power': np.random.uniform(200, 400, n)
    })
    
    # Create target with some signal and noise
    # y = 0.5 * energy_density + random_group_effect + noise
    group_effects = {f"Alloy_{i}": np.random.uniform(-5, 5) for i in range(n_groups)}
    y = 0.5 * X['energy_density'] + np.array([group_effects[g] for g in groups]) + np.random.normal(0, 2, n)
    
    return pd.DataFrame({
        'energy_density': X['energy_density'],
        'ductility': y,
        'alloy_family': groups
    })

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_mixed_effects_convergence_check(sample_lme_data, temp_output_dir):
    """
    Test that the mixed-effects model converges on a well-behaved dataset.
    This test verifies the core functionality of fit_lme_model and extract_results.
    """
    # Prepare data
    X = sample_lme_data[['energy_density']]
    y = sample_lme_data['ductility']
    groups = sample_lme_data['alloy_family']

    # Fit model
    model_result, converged, message = fit_lme_model(X, y, groups)

    # Assert convergence
    assert converged, f"Model did not converge: {message}"
    assert model_result is not None

    # Extract results
    results = extract_results(model_result, ['energy_density'])

    # Verify structure
    assert 'convergence_status' in results
    assert results['convergence_status'] == 'converged'
    assert 'fixed_effects' in results
    assert len(results['fixed_effects']) > 0

    # Verify specific fields in fixed effects
    first_effect = results['fixed_effects'][0]
    assert 'coefficient' in first_effect
    assert 'p_value' in first_effect
    assert 'ci_95_lower' in first_effect
    assert 'ci_95_upper' in first_effect

    # Verify random effects exist
    assert 'random_effects' in results
    assert len(results['random_effects']) > 0

    # Verify model statistics
    assert 'model_statistics' in results
    assert 'log_likelihood' in results['model_statistics']
    assert 'n_observations' in results['model_statistics']

def test_mixed_effects_no_convergence():
    """
    Test behavior when model fails to converge (simulated by bad data).
    """
    # Create data that might cause convergence issues (e.g., perfect multicollinearity or no variance)
    X = pd.DataFrame({'energy_density': [1.0] * 10}) # No variance
    y = pd.Series([1.0] * 10)
    groups = pd.Series(['A'] * 10)

    # This should fail or return converged=False
    model_result, converged, message = fit_lme_model(X, y, groups)
    
    # We expect it to fail or not converge due to lack of variance
    # The function should handle this gracefully
    assert model_result is None or not converged

def test_vif_calculation_logic():
    """
    Test VIF calculation logic (from T023 context).
    """
    # Create a simple dataset
    np.random.seed(42)
    X = pd.DataFrame({
        'A': np.random.rand(100),
        'B': np.random.rand(100),
        'C': np.random.rand(100)
    })
    
    # Add high correlation to A and B
    X['B'] = X['A'] * 2 + np.random.normal(0, 0.1, 100)
    
    # Calculate VIF
    vif_data = pd.DataFrame()
    vif_data["feature"] = X.columns
    vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(len(X.columns))]
    
    # Check that VIF for correlated features is high
    assert vif_data[vif_data['feature'] == 'A']['VIF'].values[0] > 5
    assert vif_data[vif_data['feature'] == 'B']['VIF'].values[0] > 5

def test_vif_independent_features():
    """
    Test VIF with independent features.
    """
    np.random.seed(42)
    X = pd.DataFrame({
        'A': np.random.rand(100),
        'B': np.random.rand(100),
        'C': np.random.rand(100)
    })
    
    vif_data = pd.DataFrame()
    vif_data["feature"] = X.columns
    vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(len(X.columns))]
    
    # VIF should be close to 1 for independent features
    assert all(vif_data['VIF'] < 5)

def test_vif_single_feature():
    """
    Test VIF with a single feature.
    """
    X = pd.DataFrame({'A': np.random.rand(100)})
    vif = variance_inflation_factor(X.values, 0)
    assert vif == 1.0 # VIF for single feature is 1

def test_vif_with_nan():
    """
    Test VIF calculation with NaN values.
    """
    X = pd.DataFrame({
        'A': [1.0, 2.0, np.nan, 4.0],
        'B': [1.0, 2.0, 3.0, 4.0]
    })
    
    # VIF should handle NaNs or raise an error depending on implementation
    # statsmodels VIF usually raises error or returns NaN
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            vif = variance_inflation_factor(X.values, 0)
            # If it doesn't raise, it might be NaN
            assert np.isnan(vif)
        except Exception:
            # Expected behavior for NaNs
            pass

def test_train_val_test_split_logic():
    """
    Test train/val/test split logic.
    """
    X = np.random.rand(100, 5)
    y = np.random.rand(100)
    
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)
    
    assert len(X_train) == 70
    assert len(X_val) == 15
    assert len(X_test) == 15

def test_loafo_split_logic():
    """
    Test Leave-One-Alloy-Family-Out split logic.
    """
    # Create data with groups
    df = pd.DataFrame({
        'feature': np.random.rand(100),
        'target': np.random.rand(100),
        'group': np.repeat(['A', 'B', 'C'], 33) + ['A'] # 34, 33, 33
    })
    
    groups = df['group'].unique()
    
    # Simulate one fold
    test_group = groups[0]
    train_df = df[df['group'] != test_group]
    test_df = df[df['group'] == test_group]
    
    assert len(train_df) + len(test_df) == len(df)
    assert len(set(train_df['group'])) == len(groups) - 1
    assert len(set(test_df['group'])) == 1

def test_split_deterministic():
    """
    Test that splits are deterministic with a fixed seed.
    """
    X = np.random.rand(100, 5)
    y = np.random.rand(100)
    
    X1, _, y1, _ = train_test_split(X, y, test_size=0.3, random_state=42)
    X2, _, y2, _ = train_test_split(X, y, test_size=0.3, random_state=42)
    
    assert np.array_equal(X1, X2)
    assert np.array_equal(y1, y2)

def test_integration_model_training_time_budget():
    """
    Integration test to ensure model training completes within time budget.
    """
    import time
    
    # Create a larger dataset to simulate real workload
    np.random.seed(42)
    n = 500
    n_groups = 10
    groups = np.repeat([f"Alloy_{i}" for i in range(n_groups)], n // n_groups)
    
    X = pd.DataFrame({
        'energy_density': np.random.uniform(50, 150, n)
    })
    
    group_effects = {f"Alloy_{i}": np.random.uniform(-5, 5) for i in range(n_groups)}
    y = 0.5 * X['energy_density'] + np.array([group_effects[g] for g in groups]) + np.random.normal(0, 2, n)
    
    start_time = time.time()
    
    model_result, converged, message = fit_lme_model(X, y, pd.Series(groups))
    
    end_time = time.time()
    
    assert end_time - start_time < 600, "Model training took too long (>600s)"
    assert converged, "Model did not converge within time budget"