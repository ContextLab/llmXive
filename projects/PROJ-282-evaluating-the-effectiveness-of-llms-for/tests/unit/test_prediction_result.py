import pytest
from src.models.prediction_result import PredictionResult, create_prediction_result
from src.models.code_snippet import CodeSnippet


class TestPredictionResultCreation:
    def test_create_valid_prediction(self):
        result = create_prediction_result(
            snippet_id="123",
            model_id="model-A",
            predicted_label="SQLi",
            confidence=0.95,
            ground_truth_label="SQLi"
        )
        assert result.snippet_id == "123"
        assert result.is_correct is True
        assert result.predicted_label == "SQLi"

    def test_create_incorrect_prediction(self):
        result = create_prediction_result(
            snippet_id="123",
            model_id="model-A",
            predicted_label="none",
            confidence=0.8,
            ground_truth_label="SQLi"
        )
        assert result.is_correct is False

    def test_confidence_bounds(self):
        # Valid bounds
        create_prediction_result("1", "m", "X", 0.0, "X")
        create_prediction_result("1", "m", "X", 1.0, "X")
        
        # Invalid bounds should raise
        with pytest.raises(ValueError):
            create_prediction_result("1", "m", "X", -0.1, "X")
        with pytest.raises(ValueError):
            create_prediction_result("1", "m", "X", 1.1, "X")

    def test_missing_required_fields(self):
        with pytest.raises(KeyError):
            # Simulating dict_to_prediction_result with missing fields
            from src.models.prediction_result import dict_to_prediction_result
            dict_to_prediction_result({"snippet_id": "1"})

class TestCreatePredictionResultFactory:
    def test_factory_calculates_correctness_case_insensitive(self):
        result = create_prediction_result(
            snippet_id="1",
            model_id="m",
            predicted_label="sqli",
            confidence=0.9,
            ground_truth_label="SQLi"
        )
        assert result.is_correct is True

    def test_factory_optional_fields(self):
        result = create_prediction_result(
            snippet_id="1",
            model_id="m",
            predicted_label="none",
            confidence=0.5,
            ground_truth_label="none",
            inference_time_ms=100.5,
            raw_response="No vulnerability found"
        )
        assert result.inference_time_ms == 100.5
        assert result.raw_response == "No vulnerability found"
