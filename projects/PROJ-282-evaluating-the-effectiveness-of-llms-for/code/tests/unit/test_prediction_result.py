import pytest
from src.models.prediction_result import PredictionResult, create_prediction_result
from src.models.code_snippet import CodeSnippet


class TestPredictionResultCreation:
    """Tests for basic PredictionResult creation and validation."""

    def test_create_with_required_fields(self):
        """Test creating a PredictionResult with only required fields."""
        result = PredictionResult(
            snippet_id="test-123",
            predicted_label="vulnerable"
        )
        
        assert result.snippet_id == "test-123"
        assert result.predicted_label == "vulnerable"
        assert result.predicted_category is None
        assert result.is_correct is None
        assert result.inference_time_ms == 0.0
        assert result.model_id is None
        assert result.confidence_score is None
        assert result.raw_output is None
        assert result.id is not None
        assert result.created_at is not None

    def test_create_with_all_fields(self):
        """Test creating a PredictionResult with all fields populated."""
        result = PredictionResult(
            snippet_id="test-456",
            predicted_label="safe",
            predicted_category="SQLi",
            is_correct=True,
            inference_time_ms=123.45,
            model_id="code-llama-7b",
            confidence_score=0.95,
            raw_output="No vulnerability detected."
        )
        
        assert result.snippet_id == "test-456"
        assert result.predicted_label == "safe"
        assert result.predicted_category == "SQLi"
        assert result.is_correct is True
        assert result.inference_time_ms == 123.45
        assert result.model_id == "code-llama-7b"
        assert result.confidence_score == 0.95
        assert result.raw_output == "No vulnerability detected."

    def test_empty_snippet_id_raises_error(self):
        """Test that empty snippet_id raises ValueError."""
        with pytest.raises(ValueError, match="snippet_id cannot be empty"):
            PredictionResult(
                snippet_id="",
                predicted_label="vulnerable"
            )

    def test_empty_predicted_label_raises_error(self):
        """Test that empty predicted_label raises ValueError."""
        with pytest.raises(ValueError, match="predicted_label cannot be empty"):
            PredictionResult(
                snippet_id="test-789",
                predicted_label=""
            )

    def test_invalid_confidence_score_raises_error(self):
        """Test that confidence_score outside [0, 1] raises ValueError."""
        with pytest.raises(ValueError, match="confidence_score must be between 0.0 and 1.0"):
            PredictionResult(
                snippet_id="test-101",
                predicted_label="vulnerable",
                confidence_score=1.5
            )
        
        with pytest.raises(ValueError, match="confidence_score must be between 0.0 and 1.0"):
            PredictionResult(
                snippet_id="test-102",
                predicted_label="vulnerable",
                confidence_score=-0.1
            )

    def test_negative_inference_time_raises_error(self):
        """Test that negative inference_time_ms raises ValueError."""
        with pytest.raises(ValueError, match="inference_time_ms cannot be negative"):
            PredictionResult(
                snippet_id="test-103",
                predicted_label="vulnerable",
                inference_time_ms=-10.0
            )


class TestCreatePredictionResultFactory:
    """Tests for the create_prediction_result factory function."""

    def test_create_from_snippet_with_ground_truth(self):
        """Test that is_correct is automatically determined when ground truth exists."""
        snippet = CodeSnippet(
            id="snippet-001",
            language="python",
            source_code="def test(): pass",
            ground_truth_label="vulnerable",
            ground_truth_category="SQLi"
        )
        
        # Prediction matches ground truth
        result = create_prediction_result(
            snippet=snippet,
            predicted_label="vulnerable"
        )
        
        assert result.snippet_id == "snippet-001"
        assert result.predicted_label == "vulnerable"
        assert result.is_correct is True

    def test_create_from_snippet_mismatched_label(self):
        """Test that is_correct is False when prediction doesn't match ground truth."""
        snippet = CodeSnippet(
            id="snippet-002",
            language="python",
            source_code="def test(): pass",
            ground_truth_label="safe",
            ground_truth_category=None
        )
        
        # Prediction does not match ground truth
        result = create_prediction_result(
            snippet=snippet,
            predicted_label="vulnerable"
        )
        
        assert result.snippet_id == "snippet-002"
        assert result.predicted_label == "vulnerable"
        assert result.is_correct is False

    def test_create_from_snippet_case_insensitive(self):
        """Test that label comparison is case-insensitive."""
        snippet = CodeSnippet(
            id="snippet-003",
            language="python",
            source_code="def test(): pass",
            ground_truth_label="Vulnerable",
            ground_truth_category=None
        )
        
        # Different case should still match
        result = create_prediction_result(
            snippet=snippet,
            predicted_label="vulnerable"
        )
        
        assert result.is_correct is True

    def test_create_from_snippet_no_ground_truth(self):
        """Test that is_correct remains None when ground truth is not available."""
        snippet = CodeSnippet(
            id="snippet-004",
            language="python",
            source_code="def test(): pass",
            ground_truth_label=None,
            ground_truth_category=None
        )
        
        result = create_prediction_result(
            snippet=snippet,
            predicted_label="safe"
        )
        
        assert result.snippet_id == "snippet-004"
        assert result.predicted_label == "safe"
        assert result.is_correct is None

    def test_create_with_explicit_is_correct(self):
        """Test that explicit is_correct overrides ground truth comparison."""
        snippet = CodeSnippet(
            id="snippet-005",
            language="python",
            source_code="def test(): pass",
            ground_truth_label="vulnerable",
            ground_truth_category=None
        )
        
        # Explicitly set is_correct to False despite matching ground truth
        result = create_prediction_result(
            snippet=snippet,
            predicted_label="vulnerable",
            is_correct=False
        )
        
        assert result.is_correct is False

    def test_create_with_optional_fields(self):
        """Test creating prediction with all optional fields."""
        snippet = CodeSnippet(
            id="snippet-006",
            language="c",
            source_code="int x = 0;",
            ground_truth_label="safe",
            ground_truth_category=None
        )
        
        result = create_prediction_result(
            snippet=snippet,
            predicted_label="safe",
            predicted_category="BufferOverflow",
            inference_time_ms=50.0,
            model_id="starcoder-base",
            confidence_score=0.88,
            raw_output="No issues found."
        )
        
        assert result.predicted_category == "BufferOverflow"
        assert result.inference_time_ms == 50.0
        assert result.model_id == "starcoder-base"
        assert result.confidence_score == 0.88
        assert result.raw_output == "No issues found."