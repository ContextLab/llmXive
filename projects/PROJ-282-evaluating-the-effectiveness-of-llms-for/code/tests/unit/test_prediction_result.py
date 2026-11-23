"""
Unit tests for the PredictionResult model generated from the contract.
"""
import pytest
import json
from src.models.prediction_result import (
    PredictionResult,
    PredictionResultSchema,
    create_prediction_result,
    prediction_result_to_dict,
    dict_to_prediction_result
)


class TestPredictionResultCreation:
    """Tests for creating PredictionResult instances."""

    def test_create_valid_prediction(self):
        """Test creating a valid prediction result."""
        result = create_prediction_result(
            snippet_id="test-123",
            predicted_label="SQLi",
            predicted_category="SQL Injection",
            is_correct=True,
            inference_time_ms=150.5
        )
        
        assert result.snippet_id == "test-123"
        assert result.predicted_label == "SQLi"
        assert result.predicted_category == "SQL Injection"
        assert result.is_correct is True
        assert result.inference_time_ms == 150.5

    def test_create_with_none_label(self):
        """Test creating a prediction with 'none' label."""
        result = create_prediction_result(
            snippet_id="test-456",
            predicted_label="none",
            predicted_category="Safe",
            is_correct=True,
            inference_time_ms=100.0
        )
        
        assert result.predicted_label == "none"
        assert result.is_correct is True

    def test_create_with_uncertain_label(self):
        """Test creating a prediction with uncertain label."""
        result = create_prediction_result(
            snippet_id="test-789",
            predicted_label="uncertain",
            predicted_category="Unknown",
            is_correct=False,
            inference_time_ms=200.25
        )
        
        assert result.predicted_label == "uncertain"
        assert result.is_correct is False


class TestPredictionResultValidation:
    """Tests for PredictionResult validation."""

    def test_missing_required_field(self):
        """Test that missing required fields raise validation error."""
        with pytest.raises(Exception):
            create_prediction_result(
                snippet_id="test-123",
                # predicted_label missing
                predicted_category="SQL Injection",
                is_correct=True,
                inference_time_ms=150.5
            )

    def test_invalid_type(self):
        """Test that invalid types are caught."""
        with pytest.raises(Exception):
            create_prediction_result(
                snippet_id="test-123",
                predicted_label=123,  # Should be string
                predicted_category="SQL Injection",
                is_correct=True,
                inference_time_ms=150.5
            )

    def test_negative_inference_time(self):
        """Test that negative inference time is allowed but unusual (schema doesn't forbid)."""
        # Pydantic allows negative numbers unless constrained
        result = create_prediction_result(
            snippet_id="test-123",
            predicted_label="SQLi",
            predicted_category="SQL Injection",
            is_correct=True,
            inference_time_ms=-1.0
        )
        assert result.inference_time_ms == -1.0


class TestPredictionResultSerialization:
    """Tests for serialization and deserialization."""

    def test_to_dict(self):
        """Test converting prediction result to dictionary."""
        result = create_prediction_result(
            snippet_id="test-123",
            predicted_label="SQLi",
            predicted_category="SQL Injection",
            is_correct=True,
            inference_time_ms=150.5
        )
        
        data = prediction_result_to_dict(result)
        
        assert data["snippet_id"] == "test-123"
        assert data["predicted_label"] == "SQLi"
        assert data["predicted_category"] == "SQL Injection"
        assert data["is_correct"] is True
        assert data["inference_time_ms"] == 150.5

    def test_from_dict(self):
        """Test creating prediction result from dictionary."""
        data = {
            "snippet_id": "test-456",
            "predicted_label": "Buffer Overflow",
            "predicted_category": "Memory Safety",
            "is_correct": False,
            "inference_time_ms": 175.0
        }
        
        result = dict_to_prediction_result(data)
        
        assert result.snippet_id == "test-456"
        assert result.predicted_label == "Buffer Overflow"
        assert result.predicted_category == "Memory Safety"
        assert result.is_correct is False
        assert result.inference_time_ms == 175.0

    def test_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        result = create_prediction_result(
            snippet_id="test-789",
            predicted_label="XSS",
            predicted_category="Cross-Site Scripting",
            is_correct=True,
            inference_time_ms=120.0
        )
        
        # Serialize to JSON
        json_str = result.model_dump_json()
        data = json.loads(json_str)
        
        # Deserialize from JSON
        result2 = PredictionResult.model_validate(data)
        
        assert result.snippet_id == result2.snippet_id
        assert result.predicted_label == result2.predicted_label
        assert result.predicted_category == result2.predicted_category
        assert result.is_correct == result2.is_correct
        assert result.inference_time_ms == result2.inference_time_ms


class TestPredictionResultFactory:
    """Tests for the factory function."""

    def test_factory_creates_instance(self):
        """Test that factory function creates a PredictionResult instance."""
        result = create_prediction_result(
            snippet_id="factory-test",
            predicted_label="RCE",
            predicted_category="Remote Code Execution",
            is_correct=True,
            inference_time_ms=300.0
        )
        
        assert isinstance(result, PredictionResult)

    def test_factory_with_all_categories(self):
        """Test factory with various vulnerability categories."""
        categories = [
            ("SQLi", "SQL Injection"),
            ("Buffer Overflow", "Memory Safety"),
            ("XSS", "Cross-Site Scripting"),
            ("RCE", "Remote Code Execution"),
            ("none", "Safe")
        ]
        
        for label, category in categories:
            result = create_prediction_result(
                snippet_id=f"test-{label}",
                predicted_label=label,
                predicted_category=category,
                is_correct=True,
                inference_time_ms=100.0
            )
            assert result.predicted_label == label
            assert result.predicted_category == category
