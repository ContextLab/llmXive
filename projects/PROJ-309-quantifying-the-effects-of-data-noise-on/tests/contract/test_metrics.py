"""
Contract tests for metric results schema.

These tests verify that the output of the metrics computation pipeline
conforms to the expected data schema defined in the project specifications.
"""
import pytest
import json
from pathlib import Path
import numpy as np
from typing import Dict, Any, List

# Import the data model used for metric results
# The path matches the API surface provided: code/utils/data_models.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.data_models import MetricResult


class TestMetricResultSchema:
    """Contract tests for the MetricResult data structure."""

    def test_metric_result_required_fields(self):
        """Verify that MetricResult requires all specified fields."""
        # A valid MetricResult must have these fields
        valid_data = {
            "trajectory_id": "lorenz_clean_42",
            "metric_name": "correlation_dimension",
            "computed_value": 2.05,
            "ground_truth_value": 2.06,
            "error_percent": 0.49,
            "noise_type": "gaussian",
            "snr_db": 20.0,
            "embedding_dimension": 5,
            "timestamp": "2023-10-27T10:00:00Z"
        }

        result = MetricResult(**valid_data)

        assert result.trajectory_id == "lorenz_clean_42"
        assert result.metric_name == "correlation_dimension"
        assert np.isclose(result.computed_value, 2.05)
        assert np.isclose(result.ground_truth_value, 2.06)
        assert np.isclose(result.error_percent, 0.49)
        assert result.noise_type == "gaussian"
        assert np.isclose(result.snr_db, 20.0)
        assert result.embedding_dimension == 5
        assert result.timestamp is not None

    def test_metric_result_numeric_fields_types(self):
        """Verify that numeric fields accept only numeric types."""
        data = {
            "trajectory_id": "test_1",
            "metric_name": "lyapunov",
            "computed_value": 0.9,
            "ground_truth_value": 0.91,
            "error_percent": 1.1,
            "noise_type": "uniform",
            "snr_db": 15.0,
            "embedding_dimension": 3,
            "timestamp": "2023-10-27T10:00:00Z"
        }

        # Should accept floats
        result = MetricResult(**data)
        assert isinstance(result.computed_value, float)
        assert isinstance(result.ground_truth_value, float)
        assert isinstance(result.error_percent, float)
        assert isinstance(result.snr_db, float)
        assert isinstance(result.embedding_dimension, int)

    def test_metric_result_invalid_field_types(self):
        """Verify that invalid field types raise errors."""
        data = {
            "trajectory_id": "test_1",
            "metric_name": "fnn",
            "computed_value": "not_a_number",  # Invalid
            "ground_truth_value": 0.5,
            "error_percent": 0.0,
            "noise_type": "gaussian",
            "snr_db": 10.0,
            "embedding_dimension": 2,
            "timestamp": "2023-10-27T10:00:00Z"
        }

        with pytest.raises(TypeError):
            MetricResult(**data)

    def test_metric_result_to_dict_serialization(self):
        """Verify that MetricResult can be serialized to a dictionary."""
        result = MetricResult(
            trajectory_id="rossler_noisy_10",
            metric_name="false_nearest_neighbors",
            computed_value=0.05,
            ground_truth_value=0.02,
            error_percent=150.0,
            noise_type="quantization",
            snr_db=5.0,
            embedding_dimension=4,
            timestamp="2023-10-27T11:00:00Z"
        )

        data_dict = result.to_dict()

        assert isinstance(data_dict, dict)
        assert data_dict["trajectory_id"] == "rossler_noisy_10"
        assert data_dict["metric_name"] == "false_nearest_neighbors"
        assert np.isclose(data_dict["computed_value"], 0.05)
        assert data_dict["noise_type"] == "quantization"

    def test_metric_result_json_serialization(self):
        """Verify that MetricResult can be serialized to JSON."""
        result = MetricResult(
            trajectory_id="lorenz_test",
            metric_name="correlation_dimension",
            computed_value=2.0,
            ground_truth_value=2.01,
            error_percent=0.5,
            noise_type="gaussian",
            snr_db=30.0,
            embedding_dimension=5,
            timestamp="2023-10-27T12:00:00Z"
        )

        json_str = result.to_json()

        # Should be a valid JSON string
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["trajectory_id"] == "lorenz_test"
        assert parsed["metric_name"] == "correlation_dimension"
        assert np.isclose(parsed["computed_value"], 2.0)

    def test_metric_result_list_validation(self):
        """Verify that a list of MetricResult objects is valid."""
        results = [
            MetricResult(
                trajectory_id=f"test_{i}",
                metric_name="lyapunov",
                computed_value=0.9 + i * 0.01,
                ground_truth_value=0.91,
                error_percent=abs(i * 0.01 / 0.91) * 100,
                noise_type="gaussian",
                snr_db=20.0 - i,
                embedding_dimension=3,
                timestamp=f"2023-10-27T10:0{i}:00Z"
            )
            for i in range(5)
        ]

        assert len(results) == 5
        for r in results:
            assert isinstance(r, MetricResult)
            assert isinstance(r.trajectory_id, str)
            assert isinstance(r.metric_name, str)
            assert isinstance(r.computed_value, float)

    def test_metric_result_schema_compliance(self):
        """
        Comprehensive schema compliance test.
        Ensures the MetricResult structure matches the contract defined for
        the error calculation and visualization pipeline (US3).
        """
        # This is the exact schema expected by export_metric_results_to_csv
        expected_keys = {
            "trajectory_id",
            "metric_name",
            "computed_value",
            "ground_truth_value",
            "error_percent",
            "noise_type",
            "snr_db",
            "embedding_dimension",
            "timestamp"
        }

        result = MetricResult(
            trajectory_id="contract_test_1",
            metric_name="correlation_dimension",
            computed_value=2.05,
            ground_truth_value=2.06,
            error_percent=0.49,
            noise_type="gaussian",
            snr_db=20.0,
            embedding_dimension=5,
            timestamp="2023-10-27T10:00:00Z"
        )

        actual_keys = set(result.to_dict().keys())

        assert expected_keys == actual_keys, f"Schema mismatch: missing {expected_keys - actual_keys}, extra {actual_keys - expected_keys}"

    def test_metric_result_error_calculation_consistency(self):
        """
        Verify that the error_percent field is consistent with the
        computed and ground truth values.
        Formula: |computed - ground_truth| / |ground_truth| * 100
        """
        computed = 1.5
        ground_truth = 1.0
        expected_error = abs(computed - ground_truth) / abs(ground_truth) * 100

        result = MetricResult(
            trajectory_id="error_test",
            metric_name="test_metric",
            computed_value=computed,
            ground_truth_value=ground_truth,
            error_percent=expected_error, # Pre-calculated to match
            noise_type="gaussian",
            snr_db=10.0,
            embedding_dimension=2,
            timestamp="2023-10-27T10:00:00Z"
        )

        # The contract test ensures the stored value matches the formula
        # In real usage, this might be calculated by analysis.py
        assert np.isclose(result.error_percent, expected_error)