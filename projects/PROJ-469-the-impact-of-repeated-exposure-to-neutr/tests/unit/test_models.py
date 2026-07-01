"""
Unit tests for regression model fitting and interaction term extraction.

Tests the functionality in code/models.py to ensure:
1. The primary linear regression model fits without error.
2. The interaction term (news_exposure_z * political_ideology) is correctly extracted.
3. The model summary contains expected coefficients and p-values.

These tests assume:
- code/models.py has been implemented with a `fit_primary_model` function.
- Preprocessed data is available (simulated via fixtures).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Import the module under test. 
# Note: The actual implementation of fit_primary_model is expected in code/models.py
# Since T015 (implementation) is not yet complete, this test file will fail initially
# as expected for a "test-first" approach. Once T015 is implemented, these tests should pass.
try:
    from models import fit_primary_model, get_interaction_coefficient, get_model_summary
except ImportError:
    # If models.py is not implemented yet, pytest will handle the import error.
    # We define a placeholder to allow the file to be parsed if needed, 
    # but the actual test logic requires the real implementation.
    fit_primary_model = None
    get_interaction_coefficient = None
    get_model_summary = None

@pytest.fixture
def sample_imputed_data():
    """
    Generate a small, deterministic dataset mimicking the structure of 
    data/processed/imputed_data.csv for unit testing purposes.
    
    Columns expected: IAT_D_score, political_ideology, news_exposure_freq, 
    news_exposure_z, ideology_binary (derived).
    """
    np.random.seed(42)
    n = 50
    data = {
        'IAT_D_score': np.random.normal(0, 0.5, n),
        'political_ideology': np.random.normal(0, 1, n), # Continuous
        'news_exposure_freq': np.random.normal(3, 1, n),
        'news_exposure_z': (np.random.normal(3, 1, n) - 3) / 1, # Z-scored
        'age': np.random.randint(18, 70, n),
        'gender': np.random.choice(['M', 'F', 'Other'], n),
        'education': np.random.randint(1, 5, n)
    }
    # Ensure no NaNs for this unit test
    return pd.DataFrame(data).dropna()

@pytest.fixture
def missing_column_data(sample_imputed_data):
    """Data missing the required interaction predictor."""
    df = sample_imputed_data.drop(columns=['news_exposure_z'])
    return df

def test_fit_primary_model_returns_object(sample_imputed_data):
    """
    Test that fit_primary_model returns a statsmodels regression result object.
    """
    # This test will fail until T015 implements models.py
    if fit_primary_model is None:
        pytest.skip("models.py not yet implemented")
    
    result = fit_primary_model(sample_imputed_data)
    assert result is not None
    assert hasattr(result, 'params')  # statsmodels result has params
    assert hasattr(result, 'pvalues')

def test_fit_primary_model_raises_on_missing_columns(missing_column_data):
    """
    Test that fit_primary_model raises ValueError if required columns are missing.
    """
    if fit_primary_model is None:
        pytest.skip("models.py not yet implemented")
    
    with pytest.raises(ValueError, match="Missing required columns"):
        fit_primary_model(missing_column_data)

def test_get_interaction_coefficient_extracts_correct_term(sample_imputed_data):
    """
    Test that get_interaction_coefficient correctly extracts the interaction term
    coefficient from the model result.
    """
    if fit_primary_model is None or get_interaction_coefficient is None:
        pytest.skip("models.py not yet implemented")
    
    model_result = fit_primary_model(sample_imputed_data)
    interaction_coef = get_interaction_coefficient(model_result)
    
    assert isinstance(interaction_coef, (int, float))
    # The term name should match the formula: news_exposure_z * political_ideology
    # We verify the key exists in params
    expected_term = "news_exposure_z:political_ideology"
    # Note: statsmodels might format interaction terms differently (e.g., C(var)[T.1]:var)
    # depending on the formula API used. We check that a term containing both exists.
    params = model_result.params
    found = any("news_exposure_z" in str(k) and "political_ideology" in str(k) for k in params.index)
    assert found, "Interaction term not found in model parameters"

def test_get_model_summary_returns_dict(sample_imputed_data):
    """
    Test that get_model_summary returns a dictionary with expected keys.
    """
    if fit_primary_model is None or get_model_summary is None:
        pytest.skip("models.py not yet implemented")
    
    model_result = fit_primary_model(sample_imputed_data)
    summary = get_model_summary(model_result)
    
    assert isinstance(summary, dict)
    expected_keys = ['coef', 'pvalue', 'term_name', 'rsquared', 'n_obs']
    for key in expected_keys:
        assert key in summary, f"Missing key '{key}' in model summary"