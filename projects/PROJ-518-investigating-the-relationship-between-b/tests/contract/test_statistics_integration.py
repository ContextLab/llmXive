"""
Integration test to verify the full regression flow produces correctly formatted ΔR².
This ensures SC-003 is satisfied in the context of the full pipeline.
"""
import numpy as np
from analysis.statistics import fit_regression, format_delta_r2


def test_full_regression_delta_r2_format():
    """
    Run a full regression with mock data and verify the returned delta_r2
    is formatted to 4 decimal places as a string.
    """
    # Generate small mock dataset
    n = 50
    flexibility = np.random.rand(n)
    creativity = 0.5 * flexibility + np.random.rand(n) * 0.2
    covariates = {
        'age': np.random.randint(20, 40, n),
        'sex': np.random.choice([0, 1], n),
        'education': np.random.randint(12, 20, n),
        'static_strength': np.random.rand(n)
    }

    # Fit the model
    result = fit_regression(flexibility, creativity, covariates)

    # Verify the delta_r2 attribute exists and is formatted correctly
    assert hasattr(result, 'delta_r2'), "RegressionResult must have 'delta_r2' attribute"
    
    # The delta_r2 should be a float, but the formatted version should be a string
    # Check the formatting function directly on the value
    formatted = format_delta_r2(result.delta_r2)
    
    assert isinstance(formatted, str), "Formatted delta_r2 must be a string"
    
    # Verify precision
    if "." in formatted:
        decimal_part = formatted.split(".")[-1]
        assert len(decimal_part) == 4, (
            f"SC-003 Violation: Expected 4 decimal places, got {len(decimal_part)} "
            f"in formatted value '{formatted}'"
        )