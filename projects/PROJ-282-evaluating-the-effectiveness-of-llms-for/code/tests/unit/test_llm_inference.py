import pytest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import re
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.llm_inference import (
    parse_llm_response,
    handle_context_truncation,
    UNCERTAIN_REGEX,
    VULNERABILITY_REGEX
)
from src.models.code_snippet import CodeSnippet
from src.utils.memory_monitor import MemoryMonitor

class TestParseLLMResponse:
    """Test the LLM response parsing logic with various inputs."""

    def test_map_sql_injection(self):
        """Test mapping SQL injection responses."""
        test_cases = [
            ("This code contains SQL injection vulnerability", "SQLi"),
            ("Potential SQLi detected here", "SQLi"),
            ("SQL injection found", "SQLi"),
        ]
        
        for response, expected_label in test_cases:
            label, confidence = parse_llm_response(response)
            assert label == expected_label
            assert confidence == 0.8

    def test_map_buffer_overflow(self):
        """Test mapping buffer overflow responses."""
        test_cases = [
            ("Buffer overflow vulnerability identified", "Buffer Overflow"),
            ("Possible overflow in this function", "Buffer Overflow"),
        ]
        
        for response, expected_label in test_cases:
            label, confidence = parse_llm_response(response)
            assert label == expected_label

    def test_map_none_vulnerability(self):
        """Test mapping 'no vulnerability' responses."""
        test_cases = [
            ("No vulnerability found", "none"),
            ("Code appears secure, no vuln detected", "none"),
        ]
        
        for response, expected_label in test_cases:
            label, confidence = parse_llm_response(response)
            assert label == expected_label

    def test_map_uncertain_responses(self):
        """Test mapping ambiguous responses to 'uncertain'."""
        test_cases = [
            ("Maybe there is a vulnerability", "uncertain"),
            ("It's unclear if this is vulnerable", "uncertain"),
            ("Possibly vulnerable, need review", "uncertain"),
            ("Likely a security issue", "uncertain"),
            ("Unknown error occurred during analysis", "uncertain"),
            ("Error in processing", "uncertain"),
            ("Not sure about this one", "uncertain"),
        ]
        
        for response, expected_label in test_cases:
            label, confidence = parse_llm_response(response)
            assert label == expected_label, f"Failed for: {response}"
            assert confidence == 0.0

    def test_map_truncation_event(self):
        """Test that truncation events are mapped to uncertain."""
        test_cases = [
            ("Response was truncated due to context window", "uncertain"),
            ("Context window exceeded, cannot analyze", "uncertain"),
        ]
        
        for response, expected_label in test_cases:
            label, confidence = parse_llm_response(response)
            assert label == expected_label
            assert confidence == 0.0

    def test_unmatched_response_defaults_to_uncertain(self):
        """Test that unmatched responses default to uncertain."""
        response = "Some random text that doesn't match any pattern"
        label, confidence = parse_llm_response(response)
        assert label == "uncertain"
        assert confidence == 0.0

class TestContextTruncation:
    """Test context window truncation handling."""

    def test_no_truncation_needed(self):
        """Test that short code doesn't get truncated."""
        code = "print('hello')"
        truncated_code, was_truncated = handle_context_truncation(code, 2048)
        assert not was_truncated
        assert truncated_code == code

    def test_truncation_triggered(self):
        """Test that long code gets truncated."""
        # Create a long code string
        code = "x = 1\n" * 1000  # ~8000 characters
        
        with patch('src.models.llm_inference.logger') as mock_logger:
            truncated_code, was_truncated = handle_context_truncation(code, 100)
            
            assert was_truncated
            assert len(truncated_code) < len(code)
            assert "... [TRUNCATED]" in truncated_code
            mock_logger.warning.assert_called()

    def test_truncation_log_format(self):
        """Test that truncation events are logged correctly."""
        code = "x = 1\n" * 1000
        
        with patch('src.models.llm_inference.logger') as mock_logger:
            handle_context_truncation(code, 100)
            
            # Verify warning was logged
            assert mock_logger.warning.called
            call_args = mock_logger.warning.call_args[0][0]
            assert "Context window truncation triggered" in call_args

class TestMemoryMonitor:
    """Test memory monitoring functionality."""

    def test_memory_monitor_initialization(self):
        """Test MemoryMonitor initialization."""
        monitor = MemoryMonitor()
        assert monitor.warning_threshold_gb > 0
        assert monitor.critical_threshold_gb > monitor.warning_threshold_gb

    def test_memory_usage_detection(self):
        """Test that memory usage can be detected."""
        monitor = MemoryMonitor()
        usage = monitor.get_memory_usage_gb()
        assert isinstance(usage, float)
        assert usage >= 0

    def test_peak_memory_tracking(self):
        """Test that peak memory is tracked."""
        monitor = MemoryMonitor()
        initial_peak = monitor.get_peak_memory_gb()
        
        # Force some memory allocation
        data = [i for i in range(100000)]
        del data
        
        peak = monitor.get_peak_memory_gb()
        assert peak >= initial_peak

    def test_gc_trigger(self):
        """Test that garbage collection can be triggered."""
        monitor = MemoryMonitor()
        usage_after_gc = monitor.force_gc()
        assert isinstance(usage_after_gc, float)

    def test_warning_threshold_check(self):
        """Test warning threshold checking."""
        # This test mocks the memory usage to test the logic
        monitor = MemoryMonitor(warning_threshold_gb=5.0, critical_threshold_gb=10.0)
        
        with patch.object(monitor, 'get_memory_usage_gb', return_value=6.0):
            is_critical = monitor.check_and_warn()
            assert not is_critical
            # Verify warning was logged
            # In a real test, we'd check the logger

    def test_critical_threshold_check(self):
        """Test critical threshold checking."""
        monitor = MemoryMonitor(warning_threshold_gb=5.0, critical_threshold_gb=10.0)
        
        with patch.object(monitor, 'get_memory_usage_gb', return_value=11.0):
            is_critical = monitor.check_and_warn()
            assert is_critical

class TestLLMInferenceIntegration:
    """Integration tests for the LLM inference module."""

    def test_regex_patterns_match_expected(self):
        """Test that regex patterns correctly match expected strings."""
        # Test uncertain patterns
        assert UNCERTAIN_REGEX.search("maybe")
        assert UNCERTAIN_REGEX.search("UNCLEAR")
        assert UNCERTAIN_REGEX.search("Possibly")
        assert UNCERTAIN_REGEX.search("likely")
        assert UNCERTAIN_REGEX.search("unknown error")
        
        # Test vulnerability patterns
        assert VULNERABILITY_REGEX.search("SQL injection")
        assert VULNERABILITY_REGEX.search("buffer overflow")
        assert VULNERABILITY_REGEX.search("no vulnerability")

    def test_snippet_processing_workflow(self):
        """Test the complete workflow of snippet processing."""
        # Create a mock snippet
        snippet = CodeSnippet(
            snippet_id="test-123",
            code="print('hello')",
            language="python",
            label="none",
            source="test"
        )
        
        # Test parsing
        label, confidence = parse_llm_response("No vulnerability found")
        assert label == "none"
        
        # Test truncation logic
        truncated, was_truncated = handle_context_truncation(snippet.code, 2048)
        assert not was_truncated

    def test_edge_case_empty_response(self):
        """Test handling of empty responses."""
        label, confidence = parse_llm_response("")
        assert label == "uncertain"
        assert confidence == 0.0

    def test_edge_case_whitespace_only(self):
        """Test handling of whitespace-only responses."""
        label, confidence = parse_llm_response("   \n\t   ")
        assert label == "uncertain"
        assert confidence == 0.0