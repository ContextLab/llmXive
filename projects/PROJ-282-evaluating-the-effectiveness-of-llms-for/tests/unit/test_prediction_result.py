"""
Unit tests for the PredictionResult model.
Verifies creation, validation, and serialization against the contract.
"""
import pytest
from src.models.prediction_result import PredictionResult, create_prediction_result, prediction_result_to_dict, dict_to_prediction_result, PredictionResultSchema


class TestPredictionResultCreation:
    def test_create_with_all_fields(self):
        result = PredictionResult(
            snippet_id="test-123",
            predicted_label="vulnerable",
            predicted_category="SQLi",
            is_correct=True,
            inference_time_ms=150.5
        )
        assert result.snippet_id == "test-123"
        assert result.predicted_label == "vulnerable"
        assert result.predicted_category == "SQLi"
        assert result.is_correct is True
        assert result.inference_time_ms == 150.5

    def test_create_factory_defaults(self):
        result = create_prediction_result()
        assert result.snippet_id is not None
        assert len(result.snippet_id) > 0
        assert result.predicted_label == "unknown"
        assert result.predicted_category == "uncertain"
        assert result.is_correct is False
        assert result.inference_time_ms == 0.0

    def test_create_factory_custom_id(self):
        result = create_prediction_result(snippet_id="custom-id")
        assert result.snippet_id == "custom-id"


class TestCreatePredictionResultFactory:
    def test_serialization_to_dict(self):
        original = PredictionResult(
            snippet_id="s-999",
            predicted_label="safe",
            predicted_category="none",
            is_correct=True,
            inference_time_ms=42.0
        )
        data = prediction_result_to_dict(original)
        assert data["snippet_id"] == "s-999"
        assert data["predicted_label"] == "safe"
        assert data["predicted_category"] == "none"
        assert data["is_correct"] is True
        assert data["inference_time_ms"] == 42.0

    def test_deserialization_from_dict(self):
        data = {
            "snippet_id": "s-888",
            "predicted_label": "vulnerable",
            "predicted_category": "Buffer Overflow",
            "is_correct": False,
            "inference_time_ms": 100.0
        }
        result = dict_to_prediction_result(data)
        assert result.snippet_id == "s-888"
        assert result.predicted_label == "vulnerable"
        assert result.predicted_category == "Buffer Overflow"
        assert result.is_correct is False
        assert result.inference_time_ms == 100.0

    def test_validation_missing_required_field(self):
        # Test that Pydantic validation catches missing required fields
        invalid_data = {
            "snippet_id": "s-777",
            "predicted_label": "vulnerable"
            # Missing required fields: predicted_category, is_correct, inference_time_ms
        }
        with pytest.raises(Exception):
            dict_to_prediction_result(invalid_data)

    def test_schema_compliance(self):
        """Verify the Pydantic schema matches the contract definition."""
        schema = PredictionResultSchema(
            snippet_id="test",
            predicted_label="test",
            predicted_category="test",
            is_correct=True,
            inference_time_ms=1.0
        )
        assert schema.snippet_id == "test"
        assert schema.predicted_label == "test"
        assert schema.predicted_category == "test"
        assert schema.is_correct is True
        assert schema.inference_time_ms == 1.0
