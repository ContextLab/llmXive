"""
Contract test for regression model output schema.

This test verifies that the statistical analysis components (which serve as
the foundation for the regression models in US3) adhere to the expected
output schema defined in the project contracts. Specifically, it ensures
that statistical tests return a dictionary containing 't_statistic', 'p_value',
and 'significant' keys, which are required inputs for the regression analysis
and bias correction logic.
"""
import pytest
import numpy as np
from code.analysis.statistical_tests import perform_two_sample_ttest


def test_regression_output_schema():
    """
    Verify that statistical tests return the expected schema for regression inputs.
    
    The regression models in US3 (T027) rely on statistical metrics to determine
    significance and fit quality. This contract test ensures the data flow
    from statistical tests to regression models is valid.
    """
    # Generate synthetic control and treatment groups for testing the schema
    # In a real US3 scenario, these would be the bias measurements from US1/US2
    np.random.seed(42)  # Reproducibility
    group_baseline = np.random.normal(loc=0.0, scale=0.1, size=50)
    group_artifact = np.random.normal(loc=0.05, scale=0.1, size=50)
    
    # Execute the statistical test
    result = perform_two_sample_ttest(group_baseline, group_artifact)
    
    # Contract: Verify the schema matches the regression model's expectations
    assert isinstance(result, dict), "Statistical test must return a dictionary."
    
    # Required keys for regression input (FR-005, SC-003)
    required_keys = {"t_statistic", "p_value", "significant"}
    assert required_keys.issubset(result.keys()), (
        f"Regression model requires keys {required_keys}, "
        f"but got {result.keys()}"
    )
    
    # Verify data types match expected schema
    assert isinstance(result["t_statistic"], (int, float, np.floating)), (
        "t_statistic must be numeric"
    )
    assert isinstance(result["p_value"], (int, float, np.floating)), (
        "p_value must be numeric"
    )
    assert isinstance(result["significant"], bool), (
        "significant must be a boolean"
    )
    
    # Verify logical consistency of the result
    if result["significant"]:
        assert result["p_value"] < 0.05, (
            "If significant is True, p_value must be < 0.05"
        )
    else:
        assert result["p_value"] >= 0.05, (
            "If significant is False, p_value must be >= 0.05"
        )