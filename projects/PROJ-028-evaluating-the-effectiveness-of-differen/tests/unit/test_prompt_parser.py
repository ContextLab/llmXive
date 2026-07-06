"""
Unit tests for code block extraction regex logic.

This module tests the extraction of Python code blocks from LLM responses,
specifically handling Markdown fenced code blocks (```python ... ```) and
standard markdown code blocks (``` ... ```).

Note: The regex logic is implemented inline here to avoid circular imports
or missing dependencies in the src/ directory before full implementation.
In a full pipeline, this would import from src/evaluation/prompts.py.
"""
import re
import pytest
from typing import List, Tuple, Optional


# Regex pattern for extracting code blocks from LLM responses.
# Matches:
# 1. ```python <content> ```
# 2. ``` <content> ``` (generic markdown block)
# It prioritizes the specific language tag if present, but falls back to generic.
CODE_BLOCK_PATTERN = re.compile(
    r'```(?:python)?\s*\n(.*?)\n```',
    re.DOTALL | re.IGNORECASE
)


def extract_code_blocks(text: str) -> List[str]:
    """
    Extract Python code blocks from a string.
    
    Args:
        text: The raw LLM response string.
        
    Returns:
        A list of extracted code strings. Returns empty list if no blocks found.
    """
    if not text:
        return []
    
    matches = CODE_BLOCK_PATTERN.findall(text)
    # Strip leading/trailing whitespace from each extracted block
    return [match.strip() for match in matches]


class TestPromptParser:
    """Test suite for code block extraction logic."""

    def test_extract_single_python_block(self):
        """Test extraction of a single Python code block."""
        input_text = """
        Here is the solution:
        ```python
        def hello():
            print("Hello, World!")
        ```
        """
        expected = 'def hello():\n    print("Hello, World!")'
        result = extract_code_blocks(input_text)
        assert len(result) == 1
        assert result[0] == expected

    def test_extract_generic_markdown_block(self):
        """Test extraction of a generic markdown code block (no language tag)."""
        input_text = """
        Here is the code:
        ```
        x = 1
        y = 2
        return x + y
        ```
        """
        expected = 'x = 1\ny = 2\nreturn x + y'
        result = extract_code_blocks(input_text)
        assert len(result) == 1
        assert result[0] == expected

    def test_extract_multiple_blocks(self):
        """Test extraction when multiple code blocks are present."""
        input_text = """
        First attempt:
        ```python
        def func1():
            pass
        ```
        Second attempt:
        ```python
        def func2():
            return True
        ```
        """
        result = extract_code_blocks(input_text)
        assert len(result) == 2
        assert "def func1()" in result[0]
        assert "def func2()" in result[1]

    def test_extract_with_trailing_whitespace(self):
        """Test that leading/trailing whitespace inside blocks is stripped."""
        input_text = """
        ```python
            def indented():
                pass
        
        ```
        """
        result = extract_code_blocks(input_text)
        assert len(result) == 1
        # The content inside should be stripped of the outer block's whitespace
        # but internal indentation should remain as part of the code logic
        # The regex captures the inner content, and .strip() is applied.
        assert result[0].startswith("def indented():")

    def test_no_code_blocks(self):
        """Test behavior when no code blocks are present."""
        input_text = "This is just plain text with no code blocks."
        result = extract_code_blocks(input_text)
        assert result == []

    def test_empty_input(self):
        """Test behavior with empty string input."""
        result = extract_code_blocks("")
        assert result == []

    def test_none_input(self):
        """Test behavior with None input."""
        result = extract_code_blocks(None)
        assert result == []

    def test_malformed_block_closing(self):
        """Test handling of blocks with missing closing fences (should not match)."""
        input_text = """
        Here is code:
        ```python
        def broken():
            pass
        """
        result = extract_code_blocks(input_text)
        assert len(result) == 0

    def test_case_insensitivity(self):
        """Test that language tags are case-insensitive."""
        input_text = """
        ```PYTHON
        x = 1
        ```
        """
        result = extract_code_blocks(input_text)
        assert len(result) == 1
        assert result[0] == "x = 1"

    def test_complex_code_content(self):
        """Test extraction of complex Python code with nested structures."""
        input_text = """
        ```python
        def solve(n):
            if n <= 1:
                return n
            return solve(n-1) + solve(n-2)
        ```
        """
        expected = "def solve(n):\n    if n <= 1:\n        return n\n    return solve(n-1) + solve(n-2)"
        result = extract_code_blocks(input_text)
        assert len(result) == 1
        assert result[0] == expected

    def test_code_with_fenced_content_inside(self):
        """Test extraction when code contains backticks (edge case)."""
        # Note: This is a known limitation of simple regex; 
        # nested fences might break extraction, but basic cases should work.
        input_text = """
        ```python
        s = "This contains `backticks` inside"
        print(s)
        ```
        """
        result = extract_code_blocks(input_text)
        assert len(result) == 1
        assert 'backticks' in result[0]