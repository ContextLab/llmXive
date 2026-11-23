"""
Contract tests for ablation utilities, specifically syntactic complexity.
"""
import pytest
from pathlib import Path
import sys

# Ensure the project code is importable
# This assumes the test is run from the project root or code directory
# Adjusting path if necessary
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from src.data.ablation_utils import calculate_syntactic_complexity, calculate_token_length


class TestSyntacticComplexityCalculator:
    """Tests for the calculate_syntactic_complexity function."""

    def test_returns_positive_for_valid_critique(self):
        """
        Verify that the function returns a numeric score > 0 for valid critiques.
        This is the primary verification requirement for T015c.
        """
        critique = "The initial answer assumes a linear progression, but the problem statement implies a geometric series, creating a fundamental logic gap."
        score = calculate_syntactic_complexity(critique)

        assert isinstance(score, float), "Score must be a float."
        assert score > 0, "Syntactic complexity score must be greater than 0 for valid text."

    def test_complex_sentence_higher_score(self):
        """
        Verify that a more syntactically complex sentence yields a higher score
        than a simple one.
        """
        simple = "The answer is wrong."
        complex_text = "Although the variable X is defined as Y, which implies Z, therefore the calculation fails because the assumption of linearity is unsupported."

        score_simple = calculate_syntactic_complexity(simple)
        score_complex = calculate_syntactic_complexity(complex_text)

        # Complex text should generally have a higher score due to longer dependencies
        # Note: This is a heuristic test; exact values depend on spaCy parsing
        assert score_complex >= score_simple, (
            f"Complex sentence score ({score_complex}) should be >= simple sentence score ({score_simple})"
        )

    def test_empty_text_raises_error(self):
        """Verify that empty text raises a ValueError."""
        with pytest.raises(ValueError):
            calculate_syntactic_complexity("")

    def test_whitespace_only_raises_error(self):
        """Verify that whitespace-only text raises a ValueError."""
        with pytest.raises(ValueError):
            calculate_syntactic_complexity("   ")

    def test_numeric_output_type(self):
        """Verify the output is always a numeric type (float)."""
        text = "This is a test critique."
        score = calculate_syntactic_complexity(text)
        assert isinstance(score, (int, float)), "Output must be numeric."


class TestTokenLengthCalculator:
    """Tests for the calculate_token_length function."""

    def test_empty_string_returns_zero(self):
        assert calculate_token_length("") == 0

    def test_single_word(self):
        # GPT2/Llama tokenizer usually splits "test" into 1 token
        length = calculate_token_length("test")
        assert length >= 1

    def test_repeated_text_increases_length(self):
        len1 = calculate_token_length("hello world")
        len2 = calculate_token_length("hello world hello world")
        assert len2 > len1
