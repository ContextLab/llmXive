"""
Unit tests for code/analysis/regression.py
Verifies coefficient recovery on synthetic data with known ground truth.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.analysis.regression import (
    fit_multiple_linear_regression,
    calculate_vif,
    generate_associational_report,
    run_analysis
)
from code.utils.exceptions import CausalLanguageViolationError
from code.utils.constants import get_vif_threshold

@pytest.fixture
def synthetic_regression_data():
    """
    Creates a synthetic dataset with known coefficients for regression testing.
    Y = 2.0 * X1 + 0.5 * X2 + 1.0 (intercept) + noise
    """
    np.random.seed(42)
    n = 500
    
    # Generate predictors
    X1 = np.random.normal(0, 1, n)
    X2 = np.random.normal(0, 1, n)
    
    # Generate outcome with known coefficients
    # Y = 1.0 (const) + 2.0 * X1 + 0.5 * X2 + noise
    noise = np.random.normal(0, 0.1, n)
    Y = 1.0 + 2.0 * X1 + 0.5 * X2 + noise
    
    df = pd.DataFrame({
        "perceived_social_validation": X1,
        "age": np.random.normal(16, 2, n),
        "gender_encoded": np.random.binomial(1, 0.5, n),
        "offline_relationships_score": np.random.normal(5, 1, n),
        "intrinsic_traits_score": np.random.normal(10, 2, n),
        "self_perception_score": Y
    })
    
    return df, {"const": 1.0, "perceived_social_validation": 2.0, "age": 0.0, "gender_encoded": 0.0, "offline_relationships_score": 0.0, "intrinsic_traits_score": 0.0}

def test_fit_multiple_linear_regression_coefficient_recovery(synthetic_regression_data):
    """
    Tests that the regression model recovers the known ground truth coefficients
    within a small tolerance.
    """
    data, true_coeffs = synthetic_regression_data
    
    results, stats = fit_multiple_linear_regression(data)
    
    # Check R-squared is high (since noise is low)
    assert stats["r_squared"] > 0.90, "R-squared should be high for this synthetic data"
    
    # Check coefficient recovery
    # We expect 'perceived_social_validation' to be ~2.0
    coef_psv = stats["coefficients"]["perceived_social_validation"]
    assert abs(coef_psv - 2.0) < 0.1, f"Coefficient for PSV should be ~2.0, got {coef_psv}"
    
    # Check p-values are significant for the main predictor
    assert stats["p_values"]["perceived_social_validation"] < 0.05, "Main predictor should be significant"

def test_calculate_vif(synthetic_regression_data):
    """
    Tests that VIF calculation returns reasonable values for uncorrelated data.
    """
    data, _ = synthetic_regression_data
    
    vif_data = calculate_vif(data)
    
    # For uncorrelated predictors, VIF should be close to 1
    for col, vif in vif_data.items():
        assert 0.9 < vif < 5.0, f"VIF for {col} should be low (uncorrelated), got {vif}"
        
    # Check threshold logic
    threshold = get_vif_threshold()
    assert all(v < threshold for v in vif_data.values()), "All VIFs should be below threshold"

def test_generate_associational_report_no_causal_language(synthetic_regression_data):
    """
    Tests that the generated report does not contain causal trigger words.
    """
    data, _ = synthetic_regression_data
    results, stats = fit_multiple_linear_regression(data)
    vif_data = calculate_vif(data)
    
    report = generate_associational_report(stats, vif_data)
    
    # Basic check: should not contain "causes"
    assert "causes" not in report.lower(), "Report should not contain 'causes'"
    assert "leads to" not in report.lower(), "Report should not contain 'leads to'"
    assert "results in" not in report.lower(), "Report should not contain 'results in'"

def test_run_analysis_causal_language_violation():
    """
    Tests that run_analysis raises CausalLanguageViolationError if the report
    contains causal language.
    """
    # Create data
    np.random.seed(42)
    n = 100
    data = pd.DataFrame({
        "perceived_social_validation": np.random.normal(0, 1, n),
        "age": np.random.normal(16, 2, n),
        "gender_encoded": np.random.binomial(1, 0.5, n),
        "offline_relationships_score": np.random.normal(5, 1, n),
        "intrinsic_traits_score": np.random.normal(10, 2, n),
        "self_perception_score": np.random.normal(10, 1, n)
    })
    
    # Mock the report generation to return a string with causal language
    with patch('code.analysis.regression.generate_associational_report') as mock_report:
        mock_report.return_value = "Social validation causes self-perception to increase."
        
        with pytest.raises(CausalLanguageViolationError) as exc_info:
            # We need to mock the file writing too to avoid side effects
            with patch('builtins.open', MagicMock()):
                run_analysis(data, "dummy_path.json")
                
        assert "Causal language violation" in str(exc_info.value)

def test_run_analysis_missing_columns():
    """
    Tests that run_analysis raises ValueError if required columns are missing.
    """
    data = pd.DataFrame({"wrong_col": [1, 2, 3]})
    
    with pytest.raises(ValueError) as exc_info:
        fit_multiple_linear_regression(data)
        
    assert "Missing required columns" in str(exc_info.value)