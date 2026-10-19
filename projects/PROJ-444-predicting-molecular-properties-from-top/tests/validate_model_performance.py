"""
Validation test for the model metrics JSON produced by T005.
Ensures the file exists, is valid JSON, and conforms to the
``model_metrics.schema.yaml`` contract.
"""

import json
from pathlib import Path

import pytest
import yaml
import jsonschema

# Paths (project‑relative)
METRICS_JSON = Path("reports") / "metrics" / "model_metrics.json"
SCHEMA_PATH = Path("specs") / "001-predicting-molecular-properties-from-top" / "contracts" / "model_metrics.schema.yaml"


def load_schema() -> dict:
    with SCHEMA_PATH.open() as f:
        return yaml.safe_load(f)


def test_model_metrics_file_exists():
    assert METRICS_JSON.is_file(), f"Expected {METRICS_JSON} to exist after training."


def test_model_metrics_is_valid_json():
    with METRICS_JSON.open() as f:
        data = json.load(f)
    assert isinstance(data, dict), "Top‑level JSON object must be a dict."


def test_model_metrics_schema_compliance():
    schema = load_schema()
    with METRICS_JSON.open() as f:
        data = json.load(f)
    jsonschema.validate(instance=data, schema=schema)


@pytest.mark.parametrize("feature_set", ["traditional", "topological", "combined"])
@pytest.mark.parametrize("model_type", ["linear", "rf"])
def test_required_fields_present(feature_set, model_type):
    with METRICS_JSON.open() as f:
        data = json.load(f)

    assert feature_set in data, f"Missing feature set '{feature_set}' in JSON."
    assert model_type in data[feature_set], f"Missing model type '{model_type}' under '{feature_set}'."

    required = [
        "r2_per_fold",
        "rmse_per_fold",
        "r2_mean",
        "r2_std",
        "rmse_mean",
        "rmse_std",
        "feature_importance",
    ]
    for field in required:
        assert field in data[feature_set][model_type], f"Missing field '{field}' for {feature_set}/{model_type}."

def test_no_nan_in_metrics():
    with METRICS_JSON.open() as f:
        data = json.load(f)
    for feat_set in data.values():
        for model_res in feat_set.values():
            for metric_name in ["r2_per_fold", "rmse_per_fold"]:
                for val in model_res[metric_name]:
                    assert not (val is None or isinstance(val, float) and (val != val)), "NaN detected in metric values."

# The test suite will be executed by the platform automatically.