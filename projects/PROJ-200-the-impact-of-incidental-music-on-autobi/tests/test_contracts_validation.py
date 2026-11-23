import json
import pathlib

import pytest
from jsonschema import Draft7Validator, ValidationError

# Load schemas
CONTRACTS_DIR = pathlib.Path(__file__).resolve().parents[1] / "contracts"

@pytest.fixture(scope="module")
def dataset_schema():
    schema_path = CONTRACTS_DIR / "dataset.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def output_schema():
    schema_path = CONTRACTS_DIR / "output.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_dataset_schema_is_valid(dataset_schema):
    # Should be a valid Draft-07 schema
    validator = Draft7Validator.check_schema(dataset_schema)  # raises if invalid

def test_output_schema_is_valid(output_schema):
    # Should be a valid Draft-07 schema
    validator = Draft7Validator.check_schema(output_schema)  # raises if invalid

def test_example_aggregated_metric_validates(dataset_schema):
    # Example instance that should validate against AggregatedMetric definition
    instance = {
        "user_id": "user_1",
        "track_id": "track_42",
        "mean_vividness": 45.3,
        "mean_valence": 0.2,
        "count_cues": 5,
        "adolescent_exposure_ratio": 0.35,
    }
    validator = Draft7Validator(dataset_schema["definitions"]["AggregatedMetric"])
    validator.validate(instance)  # should not raise

def test_example_regression_result_validates(output_schema):
    instance = {
        "term": "adolescent_exposure_ratio",
        "estimate": -9.69,
        "std_error": 7.45,
        "t_value": -1.30,
        "p_value": 0.19,
        "vif": 1.0,
    }
    validator = Draft7Validator(output_schema["definitions"]["RegressionResults"])
    validator.validate(instance)  # should not raise