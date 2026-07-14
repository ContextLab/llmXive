"""
Contract test for model output schema (US2).
"""
import json
import pytest
import pandas as pd

EXPECTED_MODEL_FIELDS = {
    "roc_auc",
    "pr_auc",
    "coefficients",
    "feature_importance",
    "model_type",
}


def test_model_output_schema(model_output: dict):
    """
    Contract test: Verify model output contains required fields.
    """
    if model_output is None:
        pytest.skip("Model output fixture not available.")

    missing = EXPECTED_MODEL_FIELDS - set(model_output.keys())
    assert not missing, f"Model output missing fields: {missing}"

    assert isinstance(model_output["roc_auc"], float)
    assert model_output["roc_auc"] >= 0.0
    assert model_output["roc_auc"] <= 1.0
