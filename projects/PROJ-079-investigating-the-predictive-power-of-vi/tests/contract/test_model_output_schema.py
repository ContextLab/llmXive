"""
Contract test for model output schema.
Verifies that model output matches spec.md FR-007 requirements.
"""
import pytest
import json
from pathlib import Path
from src.config import ARTIFACTS_PATH


def test_model_schema_validates(model_output: dict) -> None:
    """
    Assert that model output dictionary contains all required keys per FR-007.

    FR-007 specifies the model output must include:
    - r2: float (R-squared value)
    - rmse: float (Root Mean Squared Error)
    - permutation_pvalue: float (p-value from permutation test)
    - fdr_min_pvalue: float (minimum adjusted p-value after FDR correction)
    - primary_method: str (name of the primary modeling method used)

    Args:
        model_output: Dictionary containing model evaluation metrics

    Raises:
        AssertionError: If any required key is missing or has wrong type
    """
    required_keys = {
        'r2': (float, int),
        'rmse': (float, int),
        'permutation_pvalue': (float, int),
        'fdr_min_pvalue': (float, int),
        'primary_method': str
    }

    # Check all required keys exist
    missing_keys = [key for key in required_keys if key not in model_output]
    if missing_keys:
        raise AssertionError(
            f"Model output missing required keys per FR-007: {missing_keys}. "
            f"Expected keys: {list(required_keys.keys())}"
        )

    # Validate types for each key
    for key, expected_types in required_keys.items():
        value = model_output[key]
        if not isinstance(value, expected_types):
            raise AssertionError(
                f"Key '{key}' has invalid type: {type(value).__name__}. "
                f"Expected one of: {tuple(t.__name__ for t in expected_types)}"
            )

    # Validate value ranges
    if not (0.0 <= model_output['r2'] <= 1.0):
        raise AssertionError(
            f"R² value {model_output['r2']} out of valid range [0.0, 1.0]"
        )

    if model_output['rmse'] < 0:
        raise AssertionError(
            f"RMSE value {model_output['rmse']} cannot be negative"
        )

    if not (0.0 <= model_output['permutation_pvalue'] <= 1.0):
        raise AssertionError(
            f"Permutation p-value {model_output['permutation_pvalue']} "
            f"out of valid range [0.0, 1.0]"
        )

    if not (0.0 <= model_output['fdr_min_pvalue'] <= 1.0):
        raise AssertionError(
            f"FDR minimum p-value {model_output['fdr_min_pvalue']} "
            f"out of valid range [0.0, 1.0]"
        )

    if model_output['primary_method'] not in [
        'elastic_net_debiased_lasso',
        'elastic_net',
        'debiased_lasso'
    ]:
        raise AssertionError(
            f"Invalid primary_method: {model_output['primary_method']}. "
            f"Expected one of: elastic_net_debiased_lasso, elastic_net, debiased_lasso"
        )


@pytest.fixture
def valid_model_output() -> dict:
    """Provide a valid model output dictionary for testing."""
    return {
        'r2': 0.75,
        'rmse': 0.23,
        'permutation_pvalue': 0.012,
        'fdr_min_pvalue': 0.034,
        'primary_method': 'elastic_net_debiased_lasso'
    }


@pytest.fixture
def model_output_missing_key() -> dict:
    """Provide a model output missing a required key."""
    return {
        'r2': 0.75,
        'rmse': 0.23,
        # Missing permutation_pvalue
        'fdr_min_pvalue': 0.034,
        'primary_method': 'elastic_net_debiased_lasso'
    }


@pytest.fixture
def model_output_invalid_type() -> dict:
    """Provide a model output with invalid type."""
    return {
        'r2': 0.75,
        'rmse': 0.23,
        'permutation_pvalue': 0.012,
        'fdr_min_pvalue': '0.034',  # String instead of float
        'primary_method': 'elastic_net_debiased_lasso'
    }


def test_missing_key_fails(valid_model_output, model_output_missing_key):
    """Test that missing required keys cause validation failure."""
    with pytest.raises(AssertionError) as exc_info:
        test_model_schema_validates(model_output_missing_key)
    assert "missing required keys" in str(exc_info.value)


def test_invalid_type_fails(valid_model_output, model_output_invalid_type):
    """Test that invalid types cause validation failure."""
    with pytest.raises(AssertionError) as exc_info:
        test_model_schema_validates(model_output_invalid_type)
    assert "invalid type" in str(exc_info.value)


def test_out_of_range_values_fail():
    """Test that out-of-range values cause validation failure."""
    invalid_output = {
        'r2': 1.5,  # Out of range
        'rmse': 0.23,
        'permutation_pvalue': 0.012,
        'fdr_min_pvalue': 0.034,
        'primary_method': 'elastic_net_debiased_lasso'
    }
    with pytest.raises(AssertionError) as exc_info:
        test_model_schema_validates(invalid_output)
    assert "out of valid range" in str(exc_info.value)