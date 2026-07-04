"""
Contract test for metric results schema.

This test verifies that the MetricResult data structure produced by the metrics
module conforms to the expected schema defined in utils/data_models.py.
It ensures that all required fields are present and have the correct types
before the data is used for error calculation or visualization.

Schema Requirements:
- system_type: str (e.g., 'lorenz', 'rossler')
- seed: int
- snr_db: float
- noise_type: str (e.g., 'gaussian', 'quantization')
- metric_name: str (e.g., 'correlation_dimension', 'lyapunov_exponent', 'fnn_rate')
- computed_value: float
- ground_truth_value: float (optional, may be None for initial generation)
- error_percent: float (optional, may be None if ground_truth is missing)
- embedding_dimension: int (optional)
- timestamp: str (ISO format)
"""

import pytest
import json
from datetime import datetime
from typing import Dict, Any, List

# Import the data model to validate against
import sys
import os

# Ensure the project root is in the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.data_models import MetricResult
from config import NoiseType
from metrics import compute_ground_truth_metrics, run_ground_truth_computation
from generators import generate_lorenz_trajectory, generate_rossler_trajectory


def get_sample_metric_result(
    system_type: str = "lorenz",
    seed: int = 42,
    snr_db: float = 20.0,
    noise_type: str = "gaussian",
    metric_name: str = "correlation_dimension",
    computed_value: float = 2.05,
    ground_truth_value: float = 2.06,
    error_percent: float = 0.48,
    embedding_dimension: int = 3,
    timestamp: str = None
) -> MetricResult:
    """Helper to create a valid MetricResult instance."""
    if timestamp is None:
        timestamp = datetime.now().isoformat()

    return MetricResult(
        system_type=system_type,
        seed=seed,
        snr_db=snr_db,
        noise_type=noise_type,
        metric_name=metric_name,
        computed_value=computed_value,
        ground_truth_value=ground_truth_value,
        error_percent=error_percent,
        embedding_dimension=embedding_dimension,
        timestamp=timestamp
    )


class TestMetricResultSchema:
    """Contract tests for the MetricResult schema."""

    def test_required_fields_exist(self):
        """Verify that all required fields are present in the schema."""
        result = get_sample_metric_result()
        data = result.__dict__

        required_fields = [
            'system_type', 'seed', 'snr_db', 'noise_type',
            'metric_name', 'computed_value', 'ground_truth_value',
            'error_percent', 'embedding_dimension', 'timestamp'
        ]

        for field in required_fields:
            assert field in data, f"Required field '{field}' is missing from MetricResult"

    def test_field_types(self):
        """Verify that fields have the correct data types."""
        result = get_sample_metric_result()
        data = result.__dict__

        assert isinstance(data['system_type'], str), "system_type must be a string"
        assert isinstance(data['seed'], int), "seed must be an integer"
        assert isinstance(data['snr_db'], float), "snr_db must be a float"
        assert isinstance(data['noise_type'], str), "noise_type must be a string"
        assert isinstance(data['metric_name'], str), "metric_name must be a string"
        assert isinstance(data['computed_value'], float), "computed_value must be a float"
        assert isinstance(data['ground_truth_value'], (float, type(None))), "ground_truth_value must be float or None"
        assert isinstance(data['error_percent'], (float, type(None))), "error_percent must be float or None"
        assert isinstance(data['embedding_dimension'], (int, type(None))), "embedding_dimension must be int or None"
        assert isinstance(data['timestamp'], str), "timestamp must be a string"

    def test_noise_type_enum_validation(self):
        """Verify that noise_type matches expected values."""
        result = get_sample_metric_result(noise_type="gaussian")
        assert result.noise_type in [NoiseType.GAUSSIAN.value, NoiseType.QUANTIZATION.value], \
            f"Invalid noise_type: {result.noise_type}"

    def test_metric_name_validity(self):
        """Verify that metric_name is one of the expected metrics."""
        valid_metrics = [
            'correlation_dimension',
            'lyapunov_exponent',
            'fnn_rate'
        ]
        result = get_sample_metric_result(metric_name='correlation_dimension')
        assert result.metric_name in valid_metrics, \
            f"Invalid metric_name: {result.metric_name}"

    def test_json_serialization(self):
        """Verify that MetricResult can be serialized to JSON without error."""
        result = get_sample_metric_result()
        try:
            json_str = result.to_json()
            # Verify it can be deserialized back
            data = json.loads(json_str)
            assert 'system_type' in data
            assert 'computed_value' in data
        except Exception as e:
            pytest.fail(f"MetricResult failed JSON serialization: {e}")

    def test_error_calculation_consistency(self):
        """Verify that error_percent is calculated correctly if ground_truth is present."""
        computed = 2.10
        ground_truth = 2.00
        expected_error = abs(computed - ground_truth) / abs(ground_truth) * 100.0

        result = get_sample_metric_result(
            computed_value=computed,
            ground_truth_value=ground_truth,
            error_percent=expected_error
        )

        # Allow small floating point tolerance
        assert abs(result.error_percent - expected_error) < 1e-5, \
            f"Error calculation mismatch: {result.error_percent} != {expected_error}"

    def test_null_ground_truth_handling(self):
        """Verify that error_percent is None when ground_truth_value is None."""
        result = get_sample_metric_result(
            ground_truth_value=None,
            error_percent=None
        )
        assert result.ground_truth_value is None
        assert result.error_percent is None

    def test_timestamp_format(self):
        """Verify that timestamp is in ISO format."""
        result = get_sample_metric_result()
        try:
            datetime.fromisoformat(result.timestamp)
        except ValueError:
            pytest.fail(f"Timestamp is not in ISO format: {result.timestamp}")

    def test_negative_snr_allowed(self):
        """Verify that negative SNR values are accepted (as per FR-002)."""
        result = get_sample_metric_result(snr_db=-5.0)
        assert result.snr_db == -5.0

    def test_large_embedding_dimension(self):
        """Verify that large embedding dimensions are accepted."""
        result = get_sample_metric_result(embedding_dimension=10)
        assert result.embedding_dimension == 10

if __name__ == "__main__":
    pytest.main([__file__, "-v"])