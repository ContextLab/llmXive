import pytest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import re
from src.models.llm_inference import (
    InferenceConfig, get_available_ram_gb, check_memory_constraint,
    load_model_4bit_cpu, parse_llm_response, run_inference_batch,
    process_snippets_zero_shot, main
)


class TestParseLLMResponse:
    def test_parse_sql_injection(self):
        assert parse_llm_response("This contains SQL injection") == "SQLi"
        assert parse_llm_response("SQLi detected") == "SQLi"

    def test_parse_buffer_overflow(self):
        assert parse_llm_response("Buffer overflow here") == "Buffer Overflow"
        assert parse_llm_response("overflow") == "Buffer Overflow"

    def test_parse_none(self):
        assert parse_llm_response("No vulnerability") == "none"
        assert parse_llm_response("None found") == "none"

    def test_parse_uncertain(self):
        assert parse_llm_response("Maybe") == "uncertain"
        assert parse_llm_response("Unclear") == "uncertain"
        assert parse_llm_response("Unknown error") == "uncertain"

class TestMemoryCheck:
    @patch('psutil.virtual_memory')
    def test_memory_ok(self, mock_mem):
        mock_mem.return_value.available = 4 * 1024 * 1024 * 1024  # 4GB
        assert check_memory_constraint(2) is True

    @patch('psutil.virtual_memory')
    def test_memory_full(self, mock_mem):
        mock_mem.return_value.available = 1 * 1024 * 1024 * 1024  # 1GB
        assert check_memory_constraint(2) is False

class TestLLMInferenceIntegration:
    @patch('src.models.llm_inference.load_model_4bit_cpu')
    @patch('src.models.llm_inference.parse_llm_response')
    def test_run_inference_batch(self, mock_parse, mock_load):
        mock_load.return_value = MagicMock()
        mock_parse.return_value = "SQLi"
        
        from src.models.code_snippet import create_snippet
        snippets = [create_snippet("code1", "py", "src")]
        
        results = run_inference_batch(snippets, model_id="test")
        assert len(results) == 1
        assert results[0].predicted_label == "SQLi"
