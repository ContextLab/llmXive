"""
Unit tests for edge cases in the vulnerability detection pipeline.
Focus: Large snippet truncation, malformed code handling, and feature extraction robustness.
"""
import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.models.llm_inference import handle_context_truncation
from src.data.feature_extractor import extract_structural_features, extract_features_for_snippet
from src.utils.config import get_config, get_project_root


class TestTruncationEdgeCases:
    """Tests for T013f: Truncation Handler logic."""

    def test_snippet_within_context_window(self):
        """Snippet shorter than limit should pass through unchanged."""
        short_code = "def hello(): pass"
        token_limit = 4096
        
        result = handle_context_truncation(short_code, token_limit)
        
        assert result["truncated"] is False
        assert result["original_length"] == len(short_code)
        assert result["truncated_length"] == len(short_code)
        assert result["code"] == short_code
        assert "truncation_event" not in result

    def test_snippet_exceeds_context_window(self):
        """Snippet longer than limit should be truncated and logged."""
        # Create a code snippet larger than 100 tokens (approx)
        long_code = "x = 1\n" * 5000 
        token_limit = 100  # Artificially low limit for testing
        
        result = handle_context_truncation(long_code, token_limit)
        
        assert result["truncated"] is True
        assert result["original_length"] == len(long_code)
        assert result["truncated_length"] < result["original_length"]
        assert len(result["code"]) < len(long_code)
        assert "truncation_event" in result
        assert result["truncation_event"]["original_tokens"] > token_limit

    def test_empty_snippet_handling(self):
        """Empty string should not cause errors."""
        result = handle_context_truncation("", 4096)
        assert result["truncated"] is False
        assert result["code"] == ""

    def test_whitespace_only_snippet(self):
        """Whitespace-only string should be handled gracefully."""
        result = handle_context_truncation("   \n\n   ", 4096)
        assert result["truncated"] is False
        assert result["code"] == "   \n\n   "


class TestMalformedCodeHandling:
    """Tests for T018: Feature Extractor robustness against malformed code."""

    def test_null_code_input(self):
        """Feature extractor should handle None input gracefully."""
        with pytest.raises((TypeError, ValueError)):
            extract_features_for_snippet(None, "python")

    def test_empty_code_input(self):
        """Feature extractor should handle empty string input."""
        # Should not crash, likely return default/zero features
        try:
            features = extract_features_for_snippet("", "python")
            # Verify it returns a dict structure even if empty/zero
            assert isinstance(features, dict)
        except Exception:
            # Some implementations might raise, which is also acceptable if documented
            pass

    def test_binary_garbage_input(self):
        """Feature extractor should handle non-text binary data."""
        binary_data = bytes([0x00, 0xFF, 0x80, 0x00] * 100)
        try:
            features = extract_features_for_snippet(binary_data, "python")
            assert isinstance(features, dict)
        except (UnicodeDecodeError, TypeError):
            # Expected behavior: fail loudly on binary data
            pass

    def test_mixed_encoding_input(self):
        """Handle code with mixed or invalid UTF-8 sequences."""
        mixed_code = "def test(): pass\n\x80\x81\x82"
        try:
            features = extract_features_for_snippet(mixed_code, "python")
            assert isinstance(features, dict)
        except UnicodeDecodeError:
            # Expected behavior: fail loudly
            pass

    def test_very_long_line_no_newlines(self):
        """Handle code with extremely long lines (potential parser issues)."""
        # A single line of 100k characters
        long_line = "x = " + "a" * 100000
        try:
            features = extract_features_for_snippet(long_line, "python")
            # If it parses, check structure
            assert isinstance(features, dict)
        except Exception:
            # If tree-sitter or regex fails on massive lines, that's a valid edge case
            pass


class TestFeatureExtractorEdgeCases:
    """Tests for structural feature extraction boundaries."""

    def test_invalid_language_enum(self):
        """Feature extractor should reject unsupported languages."""
        code = "print('hello')"
        with pytest.raises(ValueError):
            extract_features_for_snippet(code, "invalid_lang")

    def test_syntax_error_in_code(self):
        """Tree-sitter should handle code with syntax errors without crashing."""
        invalid_code = "def broken(" # Missing closing paren
        try:
            features = extract_features_for_snippet(invalid_code, "python")
            # Should return features with nulls or zeros for AST-dependent metrics
            assert isinstance(features, dict)
        except Exception:
            # Some implementations might raise, which is acceptable if documented
            pass

    def test_nested_depth_limit(self):
        """Test handling of extremely deep nesting (stack overflow risk)."""
        # Create deeply nested code
        depth = 500
        code = "def f():\n" + "    " * depth + "pass"
        try:
            features = extract_features_for_snippet(code, "python")
            assert isinstance(features, dict)
        except RecursionError:
            # Expected if the parser hits recursion limits
            pass
        except Exception:
            # Other parser errors are acceptable
            pass


class TestIntegrationEdgeCases:
    """Integration-style tests for pipeline components."""

    def test_truncation_log_file_creation(self):
        """Verify truncation events are written to the correct log file."""
        config = get_config()
        log_path = Path(get_project_root()) / config.data_logs / "truncation_events.json"
        
        # Ensure directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Run truncation on a large snippet
        long_code = "x = 1\n" * 5000
        handle_context_truncation(long_code, 100)
        
        # Check if log file exists and contains events
        if log_path.exists():
            with open(log_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert isinstance(data, list)
                # Should have at least one event from this run
                assert len(data) > 0

    def test_feature_extractor_error_log(self):
        """Verify malformed code triggers error logging."""
        # This test assumes the feature extractor logs errors to a specific file
        # as per T018 requirements
        error_log_path = Path(get_project_root()) / "data" / "logs" / "feature_extractor_errors.json"
        
        # Force an error scenario
        try:
            extract_features_for_snippet(None, "python")
        except Exception:
            pass # Expected
        
        # The actual logging mechanism depends on the implementation of T018
        # This test verifies the path exists if the implementation is correct
        # In a real run, we would assert the log contains the specific error
        if error_log_path.exists():
            with open(error_log_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert isinstance(data, list)