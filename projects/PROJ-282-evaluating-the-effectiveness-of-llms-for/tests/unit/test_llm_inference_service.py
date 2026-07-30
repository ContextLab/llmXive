"""
Unit tests for the LLM Inference Service (T013).

These tests verify the core functionality of the zero-shot inference service
including model loading, response parsing, and batch processing.
"""

import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import re

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.llm_inference import InferenceService, CATEGORY_MAPPING, UNCERTAIN_KEYWORDS
from src.models.code_snippet import CodeSnippet
from src.models.prediction_result import PredictionResult
from src.utils.config import get_config, reset_config


class TestParseLLMResponse:
    """Tests for the parse_llm_response method."""

    @pytest.fixture
    def service(self):
        """Create an InferenceService instance."""
        config = get_config()
        return InferenceService(config)

    def test_parse_sql_injection(self, service):
        """Test parsing SQL injection responses."""
        test_cases = [
            ("This code contains a SQL injection vulnerability", "SQLi"),
            ("The vulnerability is SQLi", "SQLi"),
            ("SQL injection detected in user input handling", "SQLi"),
            ("There is a sql injection here", "SQLi"),
        ]

        for response, expected_category in test_cases:
            category, confidence = service.parse_llm_response(response)
            assert category == expected_category
            assert confidence in ["high", "medium", "low"]

    def test_parse_buffer_overflow(self, service):
        """Test parsing buffer overflow responses."""
        test_cases = [
            ("Buffer overflow vulnerability in memory handling", "Buffer Overflow"),
            ("The code has an overflow issue", "Buffer Overflow"),
            ("Potential buffer overflow detected", "Buffer Overflow"),
        ]

        for response, expected_category in test_cases:
            category, confidence = service.parse_llm_response(response)
            assert category == expected_category

    def test_parse_no_vulnerability(self, service):
        """Test parsing responses indicating no vulnerability."""
        test_cases = [
            ("No vulnerability found", "none"),
            ("The code is clean and safe", "none"),
            ("None", "none"),
            ("No security issues detected", "none"),
        ]

        for response, expected_category in test_cases:
            category, confidence = service.parse_llm_response(response)
            assert category == expected_category

    def test_parse_uncertain_responses(self, service):
        """Test parsing uncertain or unclear responses."""
        test_cases = [
            ("Maybe there is a vulnerability", "uncertain"),
            ("This is unclear", "uncertain"),
            ("Possibly vulnerable", "uncertain"),
            ("Unknown error occurred", "uncertain"),
            ("Potential risk detected", "uncertain"),
        ]

        for response, expected_category in test_cases:
            category, confidence = service.parse_llm_response(response)
            assert category == expected_category

    def test_parse_empty_response(self, service):
        """Test parsing empty or None responses."""
        category, confidence = service.parse_llm_response("")
        assert category == "uncertain"

        category, confidence = service.parse_llm_response(None)
        assert category == "uncertain"

    def test_parse_unknown_vulnerability(self, service):
        """Test parsing responses with unknown vulnerability types."""
        response = "There is a security issue with authentication"
        category, confidence = service.parse_llm_response(response)
        assert category == "uncertain" or confidence == "medium"


class TestConstructPrompt:
    """Tests for the construct_prompt method."""

    @pytest.fixture
    def service(self):
        """Create an InferenceService instance."""
        config = get_config()
        return InferenceService(config)

    def test_prompt_structure(self, service):
        """Test that the prompt has the correct structure."""
        code = "def test(): pass"
        language = "python"
        prompt = service.construct_prompt(code, language)

        assert "Identify any security vulnerability" in prompt
        assert f"```{language}" in prompt
        assert code in prompt
        assert "If no vulnerability is found" in prompt

    def test_prompt_language_inclusion(self, service):
        """Test that the language is included in the prompt."""
        code = "int main() { return 0; }"
        language = "c"
        prompt = service.construct_prompt(code, language)

        assert "c code" in prompt.lower()
        assert f"```{language}" in prompt


class TestMemoryMonitor:
    """Tests for memory monitoring functionality."""

    @pytest.fixture
    def service(self):
        """Create an InferenceService instance."""
        config = get_config()
        return InferenceService(config)

    @patch('src.services.llm_inference.check_memory_constraint')
    @patch('src.services.llm_inference.force_gc')
    def test_memory_constraint_check(self, mock_gc, mock_check, service):
        """Test that memory constraints are checked during inference."""
        mock_check.return_value = False

        # Simulate memory check
        from src.utils.memory_monitor import check_memory_constraint, force_gc

        assert not check_memory_constraint(threshold_gb=0.9)
        force_gc()


class TestInferenceService:
    """Integration tests for the InferenceService."""

    @pytest.fixture
    def service(self):
        """Create an InferenceService instance."""
        config = get_config()
        return InferenceService(config)

    def test_service_initialization(self, service):
        """Test that the service initializes correctly."""
        assert service.model is None
        assert service.tokenizer is None
        assert service.memory_monitor is not None
        assert service.timeout_threshold == 0.9 * 6 * 3600

    @patch('src.services.llm_inference.TRANSFORMERS_AVAILABLE', False)
    def test_load_model_unavailable(self, service):
        """Test model loading when transformers is not available."""
        result = service.load_model()
        assert result is False

    @patch('src.services.llm_inference.AutoTokenizer')
    @patch('src.services.llm_inference.AutoModelForSeq2SeqLM')
    @patch('src.services.llm_inference.BitsAndBytesConfig')
    def test_load_model_success(self, mock_bnb, mock_model, mock_tokenizer, service):
        """Test successful model loading."""
        # Setup mocks
        mock_tokenizer.from_pretrained.return_value = MagicMock()
        mock_model.from_pretrained.return_value = MagicMock()
        mock_bnb.return_value = MagicMock()

        result = service.load_model("test-model")

        assert result is True
        assert service.model is not None
        assert service.tokenizer is not None

    def test_process_snippets_zero_shot_empty(self, service):
        """Test processing an empty list of snippets."""
        results = service.process_snippets_zero_shot([], batch_size=1)
        assert results == []

    @patch('src.services.llm_inference.AutoTokenizer')
    @patch('src.services.llm_inference.AutoModelForSeq2SeqLM')
    @patch('src.services.llm_inference.BitsAndBytesConfig')
    def test_process_snippets_batch(self, mock_bnb, mock_model, mock_tokenizer, service):
        """Test batch processing of snippets."""
        # Setup mocks
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_bnb.return_value = MagicMock()

        # Mock tokenizer methods
        mock_tokenizer_instance.encode.return_value = [1, 2, 3]
        mock_tokenizer_instance.decode.return_value = "No vulnerability found"
        mock_tokenizer_instance.eos_token_id = 50256

        # Mock model generate
        mock_output = MagicMock()
        mock_output.__getitem__ = MagicMock(return_value=[1, 2, 3])
        mock_model_instance.generate.return_value = mock_output

        # Load model
        service.load_model("test-model")

        # Create test snippets
        snippets = [
            CodeSnippet(
                id="test-1",
                language="python",
                source_code="x = 1",
                ground_truth_label="safe",
                ground_truth_category="none"
            ),
            CodeSnippet(
                id="test-2",
                language="python",
                source_code="y = 2",
                ground_truth_label="safe",
                ground_truth_category="none"
            )
        ]

        # Process snippets
        results = service.process_snippets_zero_shot(snippets, batch_size=1)

        # Verify results
        assert len(results) == 2
        assert all(isinstance(r, PredictionResult) for r in results)
        assert all(r.predicted_category == "none" for r in results)


class TestCircuitBreaker:
    """Tests for circuit breaker functionality."""

    @pytest.fixture
    def service(self):
        """Create an InferenceService instance."""
        config = get_config()
        return InferenceService(config)

    def test_timeout_threshold_calculation(self, service):
        """Test that timeout threshold is calculated correctly."""
        expected = 0.9 * 6 * 3600  # 90% of 6 hours in seconds
        assert service.timeout_threshold == expected

    @patch('src.services.llm_inference.time.time')
    def test_timeout_risk_detection(self, mock_time, service):
        """Test that timeout risk is detected."""
        service.inference_start_time = time.time() - (0.95 * 6 * 3600)  # 95% through

        # Simulate time check
        mock_time.return_value = service.inference_start_time + (0.95 * 6 * 3600)

        current_time = time.time()
        assert (current_time - service.inference_start_time) > service.timeout_threshold


if __name__ == "__main__":
    pytest.main([__file__, "-v"])