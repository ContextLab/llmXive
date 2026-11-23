"""
Unit tests for JSON schema validation of project contracts.
Ensures data produced by simulation matches expected schemas.
"""
import json
import os
import sys
import pytest
from jsonschema import validate, ValidationError

# Determine the base path for contracts
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONTRACTS_DIR = os.path.join(BASE_DIR, "contracts")

def load_schema(schema_name):
    """Load a JSON schema from the contracts directory."""
    path = os.path.join(CONTRACTS_DIR, schema_name)
    if not os.path.exists(path):
        pytest.fail(f"Schema file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def simulation_config_schema():
    return load_schema("simulation_config.json")

@pytest.fixture
def error_metric_schema():
    return load_schema("error_metric.json")

@pytest.fixture
def p_value_distribution_schema():
    return load_schema("p_value_distribution.json")

class TestSimulationConfigSchema:
    def test_valid_config(self, simulation_config_schema):
        valid_data = {
            "dataset_id": 1234,
            "missingness_mechanism": "MCAR",
            "missingness_rate": 0.1,
            "outcome_type": "continuous",
            "imputation_method": "CC",
            "n_iterations": 100,
            "random_seed": 42
        }
        validate(instance=valid_data, schema=simulation_config_schema)

    def test_invalid_mechanism(self, simulation_config_schema):
        invalid_data = {
            "dataset_id": 1234,
            "missingness_mechanism": "INVALID",
            "missingness_rate": 0.1,
            "outcome_type": "continuous",
            "imputation_method": "CC",
            "n_iterations": 100,
            "random_seed": 42
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=simulation_config_schema)

    def test_missing_required_field(self, simulation_config_schema):
        invalid_data = {
            "dataset_id": 1234,
            "missingness_mechanism": "MCAR",
            "missingness_rate": 0.1,
            "outcome_type": "continuous",
            "imputation_method": "CC",
            "random_seed": 42
            # n_iterations missing
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=simulation_config_schema)

class TestErrorMetricSchema:
    def test_valid_metric(self, error_metric_schema):
        valid_data = {
            "condition_id": "MCAR-0.1-CC",
            "total_iterations": 100,
            "significant_count": 5,
            "empirical_type1_error": 0.05,
            "nominal_alpha": 0.05,
            "relative_deviation": 0.0,
            "is_inflated": False
        }
        validate(instance=valid_data, schema=error_metric_schema)

    def test_invalid_rate(self, error_metric_schema):
        invalid_data = {
            "condition_id": "MCAR-0.1-CC",
            "total_iterations": 100,
            "significant_count": 5,
            "empirical_type1_error": 1.5,  # Invalid: > 1.0
            "nominal_alpha": 0.05,
            "relative_deviation": 0.0,
            "is_inflated": False
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=error_metric_schema)

class TestPValueDistributionSchema:
    def test_valid_distribution(self, p_value_distribution_schema):
        valid_data = {
            "run_id": "run_001",
            "config_summary": {"dataset_id": 1234},
            "p_values": [0.01, 0.04, 0.5, 0.9],
            "statistics": {
                "mean": 0.3875,
                "median": 0.27,
                "std": 0.35,
                "min": 0.01,
                "max": 0.9,
                "count_below_0_05": 2,
                "count_below_0_01": 1
            }
        }
        validate(instance=valid_data, schema=p_value_distribution_schema)

    def test_missing_statistics(self, p_value_distribution_schema):
        invalid_data = {
            "run_id": "run_001",
            "config_summary": {"dataset_id": 1234},
            "p_values": [0.01, 0.04]
            # statistics missing
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=p_value_distribution_schema)
