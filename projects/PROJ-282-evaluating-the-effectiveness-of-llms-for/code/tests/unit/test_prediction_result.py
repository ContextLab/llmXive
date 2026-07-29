import pytest
from src.models.prediction_result import PredictionResult, create_prediction_result
from src.models.code_snippet import CodeSnippet


class TestPredictionResultCreation:
    def test_prediction_result_required_fields(self):
        """Test that a PredictionResult can be created with required fields."""
        snippet = CodeSnippet(
            snippet_id="test-123",
            code="int x = 0;",
            language="C",
            ground_truth_label="buffer_overflow",
            source_file="test.c",
            line_number=10
        )

        result = create_prediction_result(
            snippet=snippet,
            predicted_label="Buffer Overflow",
            confidence=0.95,
            model_id="test-model-v1"
        )

        assert result.snippet_id == "test-123"
        assert result.predicted_label == "Buffer Overflow"
        assert result.confidence == 0.95
        assert result.model_id == "test-model-v1"
        assert result.is_correct is None
        assert result.inference_time_ms == 0.0
        assert result.raw_response is None
        assert result.error_message is None

    def test_prediction_result_with_optional_fields(self):
        """Test that a PredictionResult handles optional fields correctly."""
        snippet = CodeSnippet(
            snippet_id="test-456",
            code="sql_query = 'SELECT * FROM users'",
            language="Python",
            ground_truth_label="sqli",
            source_file="app.py",
            line_number=5
        )

        result = create_prediction_result(
            snippet=snippet,
            predicted_label="SQLi",
            confidence=0.88,
            model_id="llama-3-8b",
            is_correct=True,
            raw_response="This code is vulnerable to SQL injection.",
            error_message=None
        )

        assert result.is_correct is True
        assert result.raw_response == "This code is vulnerable to SQL injection."
        assert result.error_message is None

    def test_prediction_result_with_error(self):
        """Test that a PredictionResult can store error information."""
        snippet = CodeSnippet(
            snippet_id="test-789",
            code="invalid code",
            language="Python",
            ground_truth_label="none",
            source_file="err.py",
            line_number=1
        )

        result = create_prediction_result(
            snippet=snippet,
            predicted_label="uncertain",
            confidence=0.0,
            model_id="failed-model",
            error_message="Inference timeout"
        )

        assert result.error_message == "Inference timeout"
        assert result.predicted_label == "uncertain"


class TestCreatePredictionResultFactory:
    def test_factory_generates_unique_timestamps(self):
        """Test that the factory generates unique timestamps for multiple results."""
        snippet = CodeSnippet(
            snippet_id="test-multi",
            code="x = 1",
            language="Python",
            ground_truth_label="none",
            source_file="multi.py",
            line_number=1
        )

        result1 = create_prediction_result(
            snippet=snippet,
            predicted_label="none",
            confidence=1.0,
            model_id="model-a"
        )

        # Small delay to ensure different timestamp
        import time
        time.sleep(0.01)

        result2 = create_prediction_result(
            snippet=snippet,
            predicted_label="none",
            confidence=1.0,
            model_id="model-b"
        )

        assert result1.timestamp != result2.timestamp

    def test_factory_inherits_snippet_id(self):
        """Test that the factory correctly inherits the snippet_id from the input."""
        test_id = "factory-test-id-999"
        snippet = CodeSnippet(
            snippet_id=test_id,
            code="y = 2",
            language="C",
            ground_truth_label="none",
            source_file="factory.c",
            line_number=1
        )

        result = create_prediction_result(
            snippet=snippet,
            predicted_label="none",
            confidence=0.5,
            model_id="test"
        )

        assert result.snippet_id == test_id