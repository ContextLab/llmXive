"""
Unit tests for the schema validation framework (T007).
These tests verify that the validator correctly accepts valid data
and rejects invalid data for ExecutionRun and RegressionModel.
"""
import pytest
import json
from datetime import datetime, timezone

from code.tests.contract.validator import (
    validate_schema,
    validate_execution_run,
    validate_regression_model,
    load_schema_from_yaml,
    validate_json_against_schema
)

# --- ExecutionRun Tests ---

def get_valid_execution_run_data():
    return {
        "run_id": "run_12345678",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "node_count": 5,
        "granularity": "medium",
        "network_conditions": {
            "injected_latency_ms": 10.0,
            "packet_loss_rate": 0.01
        },
        "metrics": {
            "wall_clock_time_seconds": 120.5,
            "throughput_ops_sec": 5000.0,
            "cpu_utilization_pct": 45.2,
            "coordination_overhead_pct": 12.5
        },
        "status": "success"
    }

def get_valid_regression_model_data():
    return {
        "model_id": "model_abcdef01",
        "model_type": "MLR",
        "formula": "throughput ~ heterogeneity * granularity + injected_latency",
        "r_squared": 0.85,
        "adjusted_r_squared": 0.82,
        "coefficients": {
            "intercept": 100.0,
            "heterogeneity": -5.0,
            "granularity_coarse": 20.0,
            "injected_latency": -0.5
        },
        "p_values": {
            "intercept": 0.001,
            "heterogeneity": 0.03,
            "granularity_coarse": 0.01,
            "injected_latency": 0.04
        },
        "interaction_terms": ["heterogeneity * granularity"],
        "fit_timestamp": datetime.now(timezone.utc).isoformat()
    }

class TestExecutionRunValidation:
    def test_execution_run_schema_valid(self):
        data = get_valid_execution_run_data()
        # Should not raise
        validate_execution_run(data)

    def test_execution_run_schema_missing_field(self):
        data = get_valid_execution_run_data()
        del data['run_id']
        with pytest.raises(SchemaValidationError):
            validate_execution_run(data)

    def test_execution_run_schema_invalid_type(self):
        data = get_valid_execution_run_data()
        data['node_count'] = "five"  # Should be int
        with pytest.raises(SchemaValidationError):
            validate_execution_run(data)

    def test_execution_run_schema_invalid_enum(self):
        data = get_valid_execution_run_data()
        data['granularity'] = "super_fine"  # Not in enum
        with pytest.raises(SchemaValidationError):
            validate_execution_run(data)

    def test_execution_run_schema_boundary_values(self):
        data = get_valid_execution_run_data()
        data['network_conditions']['packet_loss_rate'] = 1.5  # > 1.0
        with pytest.raises(SchemaValidationError):
            validate_execution_run(data)

    def test_execution_run_schema_negative_values(self):
        data = get_valid_execution_run_data()
        data['node_count'] = -1
        with pytest.raises(SchemaValidationError):
            validate_execution_run(data)

class TestRegressionModelValidation:
    def test_regression_model_schema_valid(self):
        data = get_valid_regression_model_data()
        # Should not raise
        validate_regression_model(data)

    def test_regression_model_schema_missing_coefficients(self):
        data = get_valid_regression_model_data()
        del data['coefficients']
        with pytest.raises(SchemaValidationError):
            validate_regression_model(data)

    def test_regression_model_schema_invalid_r_squared(self):
        data = get_valid_regression_model_data()
        data['r_squared'] = 1.5  # > 1.0
        with pytest.raises(SchemaValidationError):
            validate_regression_model(data)

    def test_regression_model_schema_invalid_type(self):
        data = get_valid_regression_model_data()
        data['model_type'] = 123  # Should be string
        with pytest.raises(SchemaValidationError):
            validate_regression_model(data)

    def test_regression_model_schema_missing_interaction_terms(self):
        data = get_valid_regression_model_data()
        data['interaction_terms'] = []  # minItems: 1
        with pytest.raises(SchemaValidationError):
            validate_regression_model(data)

class TestDirectSchemaValidation:
    def test_load_schema_success(self):
        schema = load_schema_from_yaml(Path(__file__).parent / "schemas" / "execution_run.yaml")
        assert 'properties' in schema
        assert 'required' in schema

    def test_validate_json_string(self):
        data = get_valid_execution_run_data()
        json_str = json.dumps(data)
        schema_path = Path(__file__).parent / "schemas" / "execution_run.yaml"
        # Should not raise
        validate_json_against_schema(json_str, schema_path, "Test")

    def test_validate_dict_against_dict(self):
        data = get_valid_execution_run_data()
        schema = load_schema_from_yaml(Path(__file__).parent / "schemas" / "execution_run.yaml")
        # Should not raise
        validate_json_against_schema(data, schema, "Test")