"""
Integration test for CoT reasoning extraction.

This test verifies that the `extract_code_from_response` function in
`src/evaluation/prompts.py` correctly isolates the final code block
from a Chain-of-Thought (CoT) generated response.

It simulates a realistic LLM output containing reasoning steps followed
by a markdown code block, ensuring the runner can extract valid Python
code for execution in the sandbox.
"""
import pytest
from src.evaluation.prompts import extract_code_from_response


class TestCoTExtraction:
    """Integration tests for Chain-of-Thought code extraction."""

    def test_extract_code_from_simple_cot(self):
        """Test extraction from a standard CoT response with reasoning and code."""
        cot_response = """
        Let's think about this step by step.
        First, we need to calculate the sum of the list.
        Then we return the result.

        Here is the code:

        ```python
        def solution(nums):
            return sum(nums)
        ```
        """
        expected_code = "def solution(nums):\n    return sum(nums)"
        extracted = extract_code_from_response(cot_response)
        assert extracted is not None, "Code extraction failed for valid CoT response"
        # Normalize whitespace for comparison
        assert extracted.strip() == expected_code.strip()

    def test_extract_code_from_cot_with_multiple_blocks(self):
        """Test that the LAST code block is extracted when multiple exist."""
        cot_response = """
        I could try approach A:
        ```python
        def bad_approach():
            pass
        ```
        But approach B is better:
        ```python
        def solution(x, y):
            return x + y
        ```
        """
        expected_code = "def solution(x, y):\n    return x + y"
        extracted = extract_code_from_response(cot_response)
        assert extracted is not None
        assert "bad_approach" not in extracted
        assert "solution" in extracted
        assert extracted.strip() == expected_code.strip()

    def test_extract_code_from_cot_no_markdown(self):
        """Test extraction when code is present but not wrapped in markdown."""
        cot_response = """
        The logic is simple.
        def solution(n):
            return n * 2
        That's it.
        """
        # The regex fallback should catch this if markdown fails
        extracted = extract_code_from_response(cot_response)
        assert extracted is not None
        assert "def solution" in extracted

    def test_extract_code_from_cot_empty_response(self):
        """Test handling of empty or whitespace-only responses."""
        extracted = extract_code_from_response("")
        assert extracted is None

        extracted = extract_code_from_response("   \n\n   ")
        assert extracted is None

    def test_extract_code_from_cot_no_code(self):
        """Test handling of response with reasoning but no code."""
        cot_response = """
        This is a very complex problem.
        I need to think about the edge cases.
        What if the input is empty?
        What if the input is negative?
        I'm not sure how to solve this.
        """
        extracted = extract_code_from_response(cot_response)
        assert extracted is None, "Should return None when no code is found"

    def test_extract_code_from_cot_indented_block(self):
        """Test extraction of code blocks with varying indentation."""
        cot_response = """
        Here is the solution:
            ```python
            def solution():
                return 42
            ```
        """
        extracted = extract_code_from_response(cot_response)
        assert extracted is not None
        assert "def solution" in extracted

    def test_extract_code_from_cot_with_trailing_text(self):
        """Test extraction when text appears after the code block."""
        cot_response = """
        ```python
        def solution(a, b):
            return a * b
        ```
        This function multiplies two numbers.
        """
        expected_code = "def solution(a, b):\n    return a * b"
        extracted = extract_code_from_response(cot_response)
        assert extracted is not None
        assert "This function" not in extracted
        assert extracted.strip() == expected_code.strip()

    def test_extract_code_from_cot_complex_python(self):
        """Test extraction with complex Python syntax (imports, classes)."""
        cot_response = """
        We need to import math.
        ```python
        import math

        class Calculator:
            def __init__(self, value):
                self.value = value

            def square(self):
                return self.value ** 2
        ```
        Done.
        """
        extracted = extract_code_from_response(cot_response)
        assert extracted is not None
        assert "import math" in extracted
        assert "class Calculator" in extracted
        assert "def square" in extracted