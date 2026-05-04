"""
Contract Test for Threshold Schema (T031).

This test validates that the threshold schema definitions in
threshold_schema.py match the expected contract per US3 requirements.

Per Constitution Principle I, every imported name must exist in the
API surface. This test imports from the schema module we just created.
"""
import pytest
from dataclasses import fields, is_dataclass
from datetime import datetime
from typing import get_type_hints, get_origin, get_args
import json

# Import from the schema module (created in this task)
from models.threshold_schema import (
    ThresholdConfig,
    ThresholdState,
    CalibrationResult,
    ThresholdUpdate
)


class TestThresholdConfig:
    """Contract tests for ThresholdConfig dataclass."""

    def test_is_dataclass(self):
        """Verify ThresholdConfig is a proper dataclass."""
        assert is_dataclass(ThresholdConfig)

    def test_required_fields_exist(self):
        """Verify all required fields are present."""
        field_names = {f.name for f in fields(ThresholdConfig)}
        required_fields = {
            "method", "percentile", "confidence_level",
            "adaptive_enabled", "update_frequency", "min_observations"
        }
        assert required_fields.issubset(field_names), \
            f"Missing required fields: {required_fields - field_names}"

    def test_field_types(self):
        """Verify field type hints are correct."""
        type_hints = get_type_hints(ThresholdConfig)
        assert type_hints.get("method") == str
        assert type_hints.get("percentile") == float
        assert type_hints.get("confidence_level") == float
        assert type_hints.get("adaptive_enabled") == bool
        assert type_hints.get("update_frequency") == int
        assert type_hints.get("min_observations") == int

    def test_default_values(self):
        """Verify sensible default values."""
        config = ThresholdConfig()
        assert config.method == "percentile"
        assert config.percentile == 95.0
        assert config.confidence_level == 0.95
        assert config.adaptive_enabled is True
        assert config.update_frequency == 100
        assert config.min_observations == 50

    def test_validation_on_init(self):
        """Verify validation catches invalid parameters."""
        with pytest.raises(ValueError):
            ThresholdConfig(percentile=150.0)  # Out of range

        with pytest.raises(ValueError):
            ThresholdConfig(confidence_level=1.5)  # Out of range

        with pytest.raises(ValueError):
            ThresholdConfig(min_observations=0)  # Too low

    def test_json_serializable(self):
        """Verify config can be serialized to JSON."""
        config = ThresholdConfig()
        config_dict = {
            "method": config.method,
            "percentile": config.percentile,
            "confidence_level": config.confidence_level,
            "adaptive_enabled": config.adaptive_enabled,
            "update_frequency": config.update_frequency,
            "min_observations": config.min_observations,
            "lower_bound_percentile": config.lower_bound_percentile,
            "upper_bound_percentile": config.upper_bound_percentile,
            "min_threshold": config.min_threshold,
            "max_threshold": config.max_threshold,
            "decay_factor": config.decay_factor,
            "window_size": config.window_size,
            "log_calibration_events": config.log_calibration_events
        }
        # Should not raise
        json_str = json.dumps(config_dict)
        assert json_str is not None


class TestThresholdState:
    """Contract tests for ThresholdState dataclass."""

    def test_is_dataclass(self):
        """Verify ThresholdState is a proper dataclass."""
        assert is_dataclass(ThresholdState)

    def test_required_fields_exist(self):
        """Verify all required fields are present."""
        field_names = {f.name for f in fields(ThresholdState)}
        required_fields = {
            "current_threshold", "lower_bound", "upper_bound",
            "calibration_count", "total_observations",
            "last_calibration_time", "threshold_history"
        }
        assert required_fields.issubset(field_names), \
            f"Missing required fields: {required_fields - field_names}"

    def test_default_values(self):
        """Verify sensible default values."""
        state = ThresholdState()
        assert state.current_threshold == 0.0
        assert state.calibration_count == 0
        assert state.total_observations == 0
        assert state.threshold_history == []

    def test_to_dict_method(self):
        """Verify to_dict method exists and works."""
        state = ThresholdState(
            current_threshold=0.95,
            calibration_count=5,
            total_observations=1000
        )
        state_dict = state.to_dict()
        assert "current_threshold" in state_dict
        assert state_dict["current_threshold"] == 0.95
        assert state_dict["calibration_count"] == 5

    def test_from_dict_method(self):
        """Verify from_dict classmethod exists and works."""
        data = {
            "current_threshold": 0.97,
            "lower_bound": 0.90,
            "upper_bound": 0.99,
            "calibration_count": 10,
            "total_observations": 5000,
            "last_calibration_time": datetime.now().isoformat(),
            "threshold_history": [0.95, 0.96, 0.97],
            "score_mean": 0.5,
            "score_std": 0.2,
            "score_percentiles": {"50": 0.5, "95": 0.9},
            "method_used": "percentile",
            "config_hash": "abc123"
        }
        state = ThresholdState.from_dict(data)
        assert state.current_threshold == 0.97
        assert state.calibration_count == 10

    def test_roundtrip_serialization(self):
        """Verify to_dict and from_dict are inverse operations."""
        original = ThresholdState(
            current_threshold=0.95,
            lower_bound=0.90,
            upper_bound=0.99,
            calibration_count=5,
            total_observations=1000,
            threshold_history=[0.90, 0.92, 0.95],
            score_mean=0.5,
            score_std=0.15,
            score_percentiles={"50": 0.5, "95": 0.9}
        )
        data = original.to_dict()
        restored = ThresholdState.from_dict(data)
        assert restored.current_threshold == original.current_threshold
        assert restored.calibration_count == original.calibration_count


class TestCalibrationResult:
    """Contract tests for CalibrationResult dataclass."""

    def test_is_dataclass(self):
        """Verify CalibrationResult is a proper dataclass."""
        assert is_dataclass(CalibrationResult)

    def test_required_fields_exist(self):
        """Verify all required fields are present."""
        field_names = {f.name for f in fields(CalibrationResult)}
        required_fields = {
            "threshold", "lower_bound", "upper_bound",
            "method", "confidence_level", "calibration_time",
            "score_count", "score_mean", "score_std",
            "score_percentiles", "calibration_quality"
        }
        assert required_fields.issubset(field_names), \
            f"Missing required fields: {required_fields - field_names}"

    def test_to_dict_method(self):
        """Verify to_dict method exists and works."""
        result = CalibrationResult(
            threshold=0.95,
            lower_bound=0.90,
            upper_bound=0.99,
            method="percentile",
            confidence_level=0.95,
            calibration_time=datetime.now(),
            score_count=1000,
            score_mean=0.5,
            score_std=0.2,
            score_percentiles={"95": 0.95},
            calibration_quality="good"
        )
        result_dict = result.to_dict()
        assert "threshold" in result_dict
        assert result_dict["calibration_quality"] == "good"


class TestThresholdUpdate:
    """Contract tests for ThresholdUpdate dataclass."""

    def test_is_dataclass(self):
        """Verify ThresholdUpdate is a proper dataclass."""
        assert is_dataclass(ThresholdUpdate)

    def test_required_fields_exist(self):
        """Verify all required fields are present."""
        field_names = {f.name for f in fields(ThresholdUpdate)}
        required_fields = {
            "timestamp", "old_threshold", "new_threshold",
            "update_reason", "observations_since_update"
        }
        assert required_fields.issubset(field_names), \
            f"Missing required fields: {required_fields - field_names}"

    def test_to_dict_method(self):
        """Verify to_dict method exists and works."""
        update = ThresholdUpdate(
            timestamp=datetime.now(),
            old_threshold=0.90,
            new_threshold=0.95,
            update_reason="periodic",
            observations_since_update=100
        )
        update_dict = update.to_dict()
        assert "timestamp" in update_dict
        assert update_dict["update_reason"] == "periodic"


class TestSchemaConsistency:
    """Cross-schema consistency tests."""

    def test_config_and_state_compatibility(self):
        """Verify ThresholdConfig and ThresholdState work together."""
        config = ThresholdConfig(percentile=95.0)
        state = ThresholdState(
            current_threshold=config.percentile / 100,
            method_used=config.method
        )
        assert state.current_threshold == 0.95
        assert state.method_used == "percentile"

    def test_all_schemas_have_serialization(self):
        """Verify all schema classes have serialization methods."""
        schemas_with_to_dict = [
            ThresholdState,
            CalibrationResult,
            ThresholdUpdate
        ]
        for schema in schemas_with_to_dict:
            assert hasattr(schema, "to_dict"), \
                f"{schema.__name__} missing to_dict method"

    def test_no_circular_imports(self):
        """Verify schema module has no circular imports."""
        # This test passes if we got here without ImportError
        assert ThresholdConfig is not None
        assert ThresholdState is not None
        assert CalibrationResult is not None
        assert ThresholdUpdate is not None
