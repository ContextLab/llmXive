import pytest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import re

# Import the module under test
from src.models.llm_inference import (
    parse_llm_response,
    InferenceConfig,
    get_available_ram_gb,
    check_memory_constraint
)
from src.models.code_snippet import CodeSnippet, create_snippet

class TestParseLLMResponse:
    """Tests for the response parsing logic including truncation and ambiguity handling."""

    def setup_method(self):
        self.config = InferenceConfig(model_name="test-model")
        self.snippet_id = "test-123"

    def test_response_vulnerable_positive(self):
        """Test detection of clear vulnerability."""
        response = "The code is vulnerable to SQL injection."
        result = parse_llm_response(response, self.snippet_id, self.config)
        assert result.predicted_label == "vulnerable"
        assert result.predicted_category == "injection"

    def test_response_safe_negative(self):
        """Test detection of safe code."""
        response = "The code appears safe and follows best practices."
        result = parse_llm_response(response, self.snippet_id, self.config)
        assert result.predicted_label == "safe"
        assert result.predicted_category == "none"

    def test_response_ambiguous_maybe(self):
        """Test mapping of 'maybe' to uncertain."""
        response = "This might be vulnerable, but it's unclear."
        result = parse_llm_response(response, self.snippet_id, self.config)
        assert result.predicted_label == "uncertain"

    def test_response_ambiguous_likely(self):
        """Test mapping of 'likely' to uncertain."""
        response = "It is likely a security issue."
        result = parse_llm_response(response, self.snippet_id, self.config)
        assert result.predicted_label == "uncertain"

    def test_response_ambiguous_possibly(self):
        """Test mapping of 'possibly' to uncertain."""
        response = "Possibly contains an overflow."
        result = parse_llm_response(response, self.snippet_id, self.config)
        assert result.predicted_label == "uncertain"

    def test_response_ambiguous_unclear(self):
        """Test mapping of 'unclear' to uncertain."""
        response = "The logic is unclear and potentially unsafe."
        result = parse_llm_response(response, self.snippet_id, self.config)
        assert result.predicted_label == "uncertain"

    def test_response_case_insensitive(self):
        """Test that ambiguity detection is case insensitive."""
        response = "MAYBE there is a bug."
        result = parse_llm_response(response, self.snippet_id, self.config)
        assert result.predicted_label == "uncertain"

    def test_response_with_truncation_event_log(self):
        """
        Verify that the logic handles context length checks.
        Note: The actual logging happens inside run_inference_batch, 
        but parse_llm_response is the core logic unit.
        We test the regex logic here.
        """
        # Long response that is still ambiguous
        response = " " * 1000 + "maybe " + " " * 1000
        result = parse_llm_response(response, self.snippet_id, self.config)
        assert result.predicted_label == "uncertain"

class TestMemoryCheck:
    """Tests for memory constraint functions."""

    @patch('src.models.llm_inference.get_available_ram_gb')
    def test_memory_sufficient(self, mock_ram):
        mock_ram.return_value = 8.0
        assert check_memory_constraint(2.0, 6.0) is True

    @patch('src.models.llm_inference.get_available_ram_gb')
    def test_memory_insufficient(self, mock_ram):
        mock_ram.return_value = 3.0
        assert check_memory_constraint(2.0, 6.0) is False

    @patch('src.models.llm_inference.get_available_ram_gb')
    def test_memory_exact_threshold(self, mock_ram):
        mock_ram.return_value = 6.0
        # Threshold is 6.0, available is 6.0 -> should pass (>=)
        assert check_memory_constraint(0.5, 6.0) is True

class TestLLMInferenceIntegration:
    """Integration tests for the inference pipeline structure."""

    def test_config_creation(self):
        config = InferenceConfig(model_name="test")
        assert config.model_name == "test"
        assert config.max_context_length == 4096

    def test_snippet_creation(self):
        snippet = create_snippet(
            source_code="x = 1",
            language="python",
            ground_truth_label="safe"
        )
        assert snippet.source_code == "x = 1"
        assert snippet.language == "python"