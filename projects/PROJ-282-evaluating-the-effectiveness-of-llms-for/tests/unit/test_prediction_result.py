"""
Unit tests for PredictionResult model.
Verifies generation from schema and basic functionality.
"""
import pytest
from src.models.prediction_result import PredictionResult, create_prediction_result
from src.models.code_snippet import CodeSnippet


class TestPredictionResultCreation:
    def test_creation_with_required_fields(self):
        """Test creating a PredictionResult with all required fields."""
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

    def test_creation_with_optional_fields(self):
        """Test creating a PredictionResult with optional fields."""
        result = PredictionResult(
            snippet_id="test-456",
            predicted_label="safe",
            predicted_category="none",
            is_correct=False,
            inference_time_ms=50.0,
            model_name="llama-2-7b",
            prompt_id="prompt-789"
        )
        
        assert result.model_name == "llama-2-7b"
        assert result.prompt_id == "prompt-789"

    def test_creation_validation_empty_snippet_id(self):
        """Test that empty snippet_id raises ValueError."""
        with pytest.raises(ValueError, match="snippet_id cannot be empty"):
            PredictionResult(
                snippet_id="",
                predicted_label="vulnerable",
                predicted_category="SQLi",
                is_correct=True,
                inference_time_ms=10.0
            )

    def test_creation_validation_negative_time(self):
        """Test that negative inference_time_ms raises ValueError."""
        with pytest.raises(ValueError, match="inference_time_ms cannot be negative"):
            PredictionResult(
                snippet_id="test-789",
                predicted_label="vulnerable",
                predicted_category="SQLi",
                is_correct=True,
                inference_time_ms=-10.0
            )


class TestCreatePredictionResultFactory:
    def test_factory_with_explicit_id(self):
        """Test factory function with explicit snippet_id."""
        result = create_prediction_result(
            snippet_id="factory-123",
            predicted_label="safe",
            predicted_category="none",
            is_correct=True,
            inference_time_ms=20.0
        )
        
        assert result.snippet_id == "factory-123"
        assert result.predicted_label == "safe"

    def test_factory_generates_uuid_if_missing(self):
        """Test factory generates a UUID if snippet_id is not provided."""
        result = create_prediction_result(
            predicted_label="uncertain",
            predicted_category="uncertain",
            is_correct=False,
            inference_time_ms=0.0
        )
        
        assert result.snippet_id is not None
        assert len(result.snippet_id) > 0

    def test_factory_infers_correctness_from_snippet(self):
        """Test factory infers is_correct from CodeSnippet ground truth."""
        # Create a mock CodeSnippet with ground truth
        snippet = CodeSnippet(
            id="mock-snippet",
            language="python",
            source_code="x = 1",
            ground_truth_label="vulnerable",
            ground_truth_category="SQLi"
        )
        
        # Predict "vulnerable" -> should be correct
        result_correct = create_prediction_result(
            predicted_label="vulnerable",
            predicted_category="SQLi",
            code_snippet=snippet
        )
        assert result_correct.is_correct is True
        
        # Predict "safe" -> should be incorrect
        result_incorrect = create_prediction_result(
            predicted_label="safe",
            predicted_category="none",
            code_snippet=snippet
        )
        assert result_incorrect.is_correct is False

    def test_factory_default_values(self):
        """Test factory default values for missing arguments."""
        result = create_prediction_result()
        
        assert result.predicted_label == "uncertain"
        assert result.predicted_category == "uncertain"
        assert result.is_correct is False
        assert result.inference_time_ms == 0.0
        assert result.model_name is None
