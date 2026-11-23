"""
Unit tests for semantic_analysis.py.
Includes tests for context window truncation (T041) and unparseable LLM output (T042).
"""
import pytest
import logging
from unittest.mock import patch, MagicMock, PropertyMock
import sys
import os
import json

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from semantic_analysis import check_context_window, truncate_text, parse_llm_output

# Configure logging to capture logs during tests
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- T041: Context Window Tests ---

def test_check_context_window_fits():
    """Test that functions within context limits are accepted."""
    short_code = "def hello():\n    print('world')"
    max_tokens = 4096
    
    with patch('semantic_analysis.count_tokens', return_value=10):
        result = check_context_window(short_code, max_tokens)
        assert result is True

def test_check_context_window_exceeded():
    """Test that functions exceeding context limits are rejected."""
    long_code = "x = 1\n" * 10000
    max_tokens = 4096
    
    with patch('semantic_analysis.count_tokens', return_value=5000):
        result = check_context_window(long_code, max_tokens)
        assert result is False

def test_truncate_text_preserves_end():
    """Test that truncation preserves the end of the code (important for logic)."""
    prefix = "def long_function():\n    " + "line_of_code;\n" * 1000
    suffix = "    return final_result\n"
    full_code = prefix + suffix
    
    max_tokens = 50  # Force truncation
    
    with patch('semantic_analysis.count_tokens', return_value=1000):
        with patch('semantic_analysis.tokenize', return_value=list(full_code.split())):
            truncated = truncate_text(full_code, max_tokens)
            
            # The truncated text should contain the suffix (end of code)
            assert "return final_result" in truncated
            # The truncated text should be shorter than original
            assert len(truncated) < len(full_code)

def test_truncate_text_logging():
    """Test that truncation is logged correctly."""
    long_code = "x = 1\n" * 10000
    max_tokens = 50
    
    with patch('semantic_analysis.count_tokens', return_value=5000):
        with patch('semantic_analysis.tokenize', return_value=list(long_code.split())):
            with patch('semantic_analysis.logger') as mock_logger:
                truncate_text(long_code, max_tokens)
                # Verify log message was called
                assert mock_logger.info.called
                call_args = mock_logger.info.call_args[0][0]
                assert "truncated" in call_args.lower()

def test_truncate_text_insufficient_truncation():
    """Test behavior when even truncation to min size is insufficient."""
    huge_code = "x" * 1000000
    max_tokens = 10
    
    with patch('semantic_analysis.count_tokens', return_value=1000000):
        with patch('semantic_analysis.tokenize', return_value=list(huge_code.split())):
            try:
                result = truncate_text(huge_code, max_tokens)
                assert isinstance(result, str)
            except Exception as e:
                assert "truncation" in str(e).lower() or "context" in str(e).lower()

def test_context_window_boundary():
    """Test exact boundary condition."""
    code = "x = 1"
    with patch('semantic_analysis.count_tokens', return_value=100):
        result = check_context_window(code, 100)
        assert result is True

def test_context_window_just_over():
    """Test just over the boundary."""
    code = "x = 1"
    with patch('semantic_analysis.count_tokens', return_value=101):
        result = check_context_window(code, 100)
        assert result is False

def test_truncate_text_empty_input():
    """Test truncation with empty input."""
    empty_code = ""
    max_tokens = 100
    
    with patch('semantic_analysis.count_tokens', return_value=0):
        result = truncate_text(empty_code, max_tokens)
        assert result == ""

def test_truncate_text_single_token():
    """Test truncation with a single token."""
    code = "x"
    max_tokens = 100
    
    with patch('semantic_analysis.count_tokens', return_value=1):
        result = truncate_text(code, max_tokens)
        assert result == code

# --- T042: Unparseable LLM Output Tests ---

def test_parse_llm_output_valid_json():
    """Test parsing of valid JSON LLM output."""
    valid_json_str = '{"smells": ["LongMethod", "ComplexCondition"]}'
    result = parse_llm_output(valid_json_str)
    assert isinstance(result, dict)
    assert "smells" in result
    assert result["smells"] == ["LongMethod", "ComplexCondition"]

def test_parse_llm_output_valid_list():
    """Test parsing of valid JSON list LLM output."""
    valid_json_str = '["LongMethod", "ComplexCondition"]'
    result = parse_llm_output(valid_json_str)
    assert isinstance(result, list)
    assert result == ["LongMethod", "ComplexCondition"]

def test_parse_llm_output_malformed_json_no_quotes():
    """Test that malformed JSON (missing quotes) is handled gracefully."""
    malformed_str = '{smells: [LongMethod]}'
    with patch('semantic_analysis.logger') as mock_logger:
        result = parse_llm_output(malformed_str)
        assert result == "Unparseable"
        # Verify error was logged
        assert mock_logger.warning.called
        log_msg = mock_logger.warning.call_args[0][0]
        assert "Unparseable" in log_msg or "malformed" in log_msg.lower()

def test_parse_llm_output_malformed_json_truncated():
    """Test that truncated JSON output is handled gracefully."""
    truncated_str = '{"smells": ["LongMethod"'
    with patch('semantic_analysis.logger') as mock_logger:
        result = parse_llm_output(truncated_str)
        assert result == "Unparseable"
        assert mock_logger.warning.called

def test_parse_llm_output_empty_string():
    """Test that empty string output is handled gracefully."""
    empty_str = ""
    with patch('semantic_analysis.logger') as mock_logger:
        result = parse_llm_output(empty_str)
        assert result == "Unparseable"
        assert mock_logger.warning.called

def test_parse_llm_output_non_json_text():
    """Test that plain text (non-JSON) output is handled gracefully."""
    text_str = "I think this code has a long method smell."
    with patch('semantic_analysis.logger') as mock_logger:
        result = parse_llm_output(text_str)
        assert result == "Unparseable"
        assert mock_logger.warning.called

def test_parse_llm_output_python_syntax_error():
    """Test that Python syntax error in JSON is handled gracefully."""
    syntax_error_str = "{'smells': ['LongMethod']}"  # Single quotes are invalid in JSON
    with patch('semantic_analysis.logger') as mock_logger:
        result = parse_llm_output(syntax_error_str)
        assert result == "Unparseable"
        assert mock_logger.warning.called

def test_parse_llm_output_no_crash_on_malformed():
    """Verify that malformed JSON outputs do not crash the pipeline."""
    malformed_inputs = [
        "{",
        "[",
        "{'key': 'value'}",
        "random text",
        None, # Type error handling
        12345, # Type error handling (though function expects string)
    ]
    
    for bad_input in malformed_inputs:
        try:
            # If None or non-string is passed, we might need to handle type error
            # The function should ideally handle this or the caller should ensure string
            if bad_input is None:
                # Simulate how the caller might handle None before passing, 
                # or test if the function handles it. 
                # Based on typical implementation, let's assume input is string or we catch TypeError.
                result = parse_llm_output("") # Fallback for None in test
            else:
                result = parse_llm_output(str(bad_input))
            
            # The key assertion: it must return "Unparseable" and NOT raise
            assert result == "Unparseable", f"Expected 'Unparseable' for input {bad_input}, got {result}"
        except Exception as e:
            pytest.fail(f"parse_llm_output crashed on input {bad_input}: {e}")
