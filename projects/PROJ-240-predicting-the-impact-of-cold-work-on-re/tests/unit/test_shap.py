"""Unit tests for SHAP interaction calculation logic.

This module tests the SHAP interaction value computation for the kinetic model,
specifically verifying:
1. The model can be explained with TreeExplainer
2. Interaction values are computed correctly for interaction features
3. Interaction values sum to the expected model output
4. The interaction matrix has correct dimensions
"""

import os
import sys
import pickle
import json
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

try:
    import shap
    from sklearn.ensemble import RandomForestRegressor
except ImportError:
    # If shap or sklearn is not available, skip tests
    pytest.skip("shap or sklearn not available", allow_module_level=True)

# Import the functions we are testing from evaluate.py (where SHAP logic lives)
# Since evaluate.py is not fully implemented yet, we test the core SHAP logic directly
# This ensures the test framework is in place for when evaluate.py is implemented


def create_test_model_and_data():
    """Create a small deterministic model and dataset for testing."""
    np.random.seed(42)
    n_samples = 100

    # Create synthetic features matching the project schema
    data = {
        'cold_work_pct': np.random.uniform(0, 100, n_samples),
        'Mn_wt': np.random.uniform(0, 1, n_samples),
        'Mg_wt': np.random.uniform(0, 1, n_samples),
        'Si_wt': np.random.uniform(0, 1, n_samples),
        'Cu_wt': np.random.uniform(0, 1, n_samples),
        'annealing_temp_K': np.random.uniform(300, 800, n_samples),
        # Interaction features
        'cold_work_Mn': np.random.uniform(0, 100, n_samples),
        'cold_work_Mg': np.random.uniform(0, 100, n_samples),
        'cold_work_Si': np.random.uniform(0, 100, n_samples),
        'cold_work_Cu': np.random.uniform(0, 100, n_samples),
    }

    df = pd.DataFrame(data)
    X = df.drop(columns=['cold_work_pct', 'Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt', 'annealing_temp_K'])
    y = np.random.uniform(10, 100, n_samples)  # time_to_peak_min

    # Train a simple model
    model = RandomForestRegressor(n_estimators=10, random_state=42, max_depth=3)
    model.fit(X, y)

    return model, X, y, df


def test_shap_explainer_initialization():
    """Test that TreeExplainer can be initialized with our model."""
    model, X, y, _ = create_test_model_and_data()

    # This should not raise an exception
    explainer = shap.TreeExplainer(model)
    assert explainer is not None
    assert explainer.model is not None


def test_shap_interaction_computation():
    """Test that SHAP interaction values can be computed."""
    model, X, y, _ = create_test_model_and_data()

    explainer = shap.TreeExplainer(model)

    # Compute SHAP interaction values
    # nsamples=100 for determinism and speed in tests
    shap_values = explainer.shap_values(X[:10], nsamples=100)

    # shap_values should be a list or array
    assert shap_values is not None
    assert len(shap_values) > 0


def test_shap_interaction_matrix_shape():
    """Test that SHAP interaction matrix has correct dimensions."""
    model, X, y, _ = create_test_model_and_data()

    explainer = shap.TreeExplainer(model)

    # For interaction values, shap_values should be a 3D array:
    # (n_samples, n_features, n_features)
    shap_interaction = explainer.shap_interaction_values(X[:5], nsamples=50)

    # Check dimensions
    assert len(shap_interaction.shape) == 3
    n_samples, n_features, _ = shap_interaction.shape
    assert n_samples == 5
    assert n_features == X.shape[1]


def test_shap_interaction_sum_to_output():
    """Test that sum of SHAP interaction values equals model output minus base value."""
    model, X, y, _ = create_test_model_and_data()

    explainer = shap.TreeExplainer(model)
    base_value = explainer.expected_value

    # Compute interaction values
    shap_interaction = explainer.shap_interaction_values(X[:3], nsamples=50)

    # Sum over all features should give SHAP values for main effects
    # Sum of all interactions should equal model output - base value
    shap_sum = np.sum(shap_interaction, axis=(1, 2))

    # Get model predictions
    predictions = model.predict(X[:3])

    # Check that sum of interactions approximates predictions - base value
    # Allow for small numerical differences due to sampling
    expected = predictions - base_value
    np.testing.assert_allclose(shap_sum, expected, rtol=0.1)


def test_shap_interaction_for_interaction_features():
    """Test that interaction terms have non-zero SHAP interaction values."""
    model, X, y, _ = create_test_model_and_data()

    explainer = shap.TreeExplainer(model)
    shap_interaction = explainer.shap_interaction_values(X[:10], nsamples=50)

    # The interaction features should have non-zero interaction values
    # with their corresponding main effects
    interaction_feature_indices = [6, 7, 8, 9]  # cold_work_Mn, cold_work_Mg, etc.

    for i in interaction_feature_indices:
        # Check that this feature has non-zero interaction with itself
        # and with other features
        mean_interaction = np.mean(np.abs(shap_interaction[:, i, i]))
        assert mean_interaction > 0, f"Feature {i} has zero self-interaction"


def test_shap_interaction_with_real_model_artifact():
    """Test SHAP interaction with a saved model artifact (if it exists)."""
    # Check if model artifact exists
    model_path = project_root / "artifacts" / "models" / "kinetic_model.pkl"

    if not model_path.exists():
        pytest.skip("kinetic_model.pkl not found, skipping real model test")

    # Load the model
    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    # Load the engineered features data
    data_path = project_root / "data" / "processed" / "engineered_features.csv"

    if not data_path.exists():
        pytest.skip("engineered_features.csv not found, skipping real data test")

    df = pd.read_csv(data_path)

    # Use only features that exist in the model
    feature_names = model.feature_names_in_ if hasattr(model, 'feature_names_in_') else None
    if feature_names is None:
        # Fallback: use all columns except target
        X = df.drop(columns=['time_to_peak_min'])
    else:
        X = df[feature_names]

    # Test SHAP interaction computation
    explainer = shap.TreeExplainer(model)
    shap_interaction = explainer.shap_interaction_values(X[:5], nsamples=20)

    assert shap_interaction is not None
    assert len(shap_interaction.shape) == 3


def test_shap_interaction_determinism():
    """Test that SHAP interaction values are deterministic with fixed seed."""
    model, X, y, _ = create_test_model_and_data()

    explainer = shap.TreeExplainer(model)

    # Run twice with same parameters
    shap1 = explainer.shap_interaction_values(X[:3], nsamples=50)
    shap2 = explainer.shap_interaction_values(X[:3], nsamples=50)

    # Results should be identical (deterministic with fixed random state in model)
    np.testing.assert_array_almost_equal(shap1, shap2, decimal=5)


def test_shap_interaction_output_format():
    """Test that SHAP interaction output can be serialized to JSON."""
    model, X, y, _ = create_test_model_and_data()

    explainer = shap.TreeExplainer(model)
    shap_interaction = explainer.shap_interaction_values(X[:2], nsamples=20)

    # Convert to list for JSON serialization
    shap_list = shap_interaction.tolist()

    # Should be serializable
    json_str = json.dumps(shap_list)
    assert len(json_str) > 0

    # Should be deserializable
    shap_loaded = json.loads(json_str)
    assert len(shap_loaded) == 2


def test_shap_interaction_with_pure_aluminum_flag():
    """Test SHAP interaction handling when pure_aluminum_flag is set."""
    # Create a dataset with zero variance in composition (pure aluminum)
    np.random.seed(42)
    n_samples = 50

    data = {
        'cold_work_pct': np.random.uniform(0, 100, n_samples),
        'Mn_wt': np.zeros(n_samples),  # Zero variance
        'Mg_wt': np.zeros(n_samples),
        'Si_wt': np.zeros(n_samples),
        'Cu_wt': np.zeros(n_samples),
        'annealing_temp_K': np.random.uniform(300, 800, n_samples),
        'cold_work_Mn': np.zeros(n_samples),
        'cold_work_Mg': np.zeros(n_samples),
        'cold_work_Si': np.zeros(n_samples),
        'cold_work_Cu': np.zeros(n_samples),
    }

    df = pd.DataFrame(data)
    X = df.drop(columns=['cold_work_pct', 'Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt', 'annealing_temp_K'])
    y = np.random.uniform(10, 100, n_samples)

    model = RandomForestRegressor(n_estimators=10, random_state=42, max_depth=3)
    model.fit(X, y)

    # SHAP should still work, but interaction values for zero-variance features
    # should be zero or very small
    explainer = shap.TreeExplainer(model)
    shap_interaction = explainer.shap_interaction_values(X[:5], nsamples=20)

    # Check that interaction features involving zero-variance columns have near-zero values
    interaction_indices = [6, 7, 8, 9]
    for i in interaction_indices:
        mean_val = np.mean(np.abs(shap_interaction[:, :, i]))
        # These should be very small due to zero variance in underlying features
        assert mean_val < 0.1, f"Interaction feature {i} has unexpectedly high values"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])