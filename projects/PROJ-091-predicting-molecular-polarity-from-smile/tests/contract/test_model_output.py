"""
Contract test for the model output metrics artifact.
Verifies that data/results/model_metrics.json exists and conforms
to the ModelOutput Pydantic schema.
"""
import pytest
import json
from pathlib import Path
from tests.contract.validators import ModelOutput

# Define the path to the expected model metrics artifact
# Based on tasks.md T104 and plan.md
MODEL_METRICS_JSON = Path("data/results/model_metrics.json")

def test_model_metrics_schema():
    """
    Validate that the model metrics JSON exists and contains 
    the required metrics (R2, RMSE, baseline_R2) with valid values.
    """
    # 1. Check existence
    if not MODEL_METRICS_JSON.exists():
        pytest.fail(f"Required artifact missing: {MODEL_METRICS_JSON}")

    # 2. Load JSON data
    with open(MODEL_METRICS_JSON, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Failed to decode JSON from {MODEL_METRICS_JSON}: {e}")

    # 3. Validate against Pydantic model
    try:
        ModelOutput(**data)
    except Exception as e:
        pytest.fail(f"Model metrics failed schema validation: {e}")