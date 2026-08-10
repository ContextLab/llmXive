import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from code.data.download_gsm8k import verify_solution_correctness

class TestSolutionVerification:
    """
    Unit tests for the GSM8K solution verification logic.
    """

    def test_valid_standard_format(self):
        """Test that a standard GSM8K answer with #### is accepted."""
        example = {
            "question": "If John has 5 apples and buys 3 more, how many does he have?",
            "answer": "John starts with 5 apples. He buys 3 more. 5 + 3 = 8. #### 8"
        }
        assert verify_solution_correctness(example) is True

    def test_valid_decimal_format(self):
        """Test that decimal answers are accepted."""
        example = {
            "question": "What is 10 divided by 3?",
            "answer": "10 / 3 is approximately 3.333. #### 3.333"
        }
        assert verify_solution_correctness(example) is True

    def test_missing_hash_tag(self):
        """Test that answers without #### are rejected."""
        example = {
            "question": "What is 2+2?",
            "answer": "The answer is 4."
        }
        assert verify_solution_correctness(example) is False

    def test_empty_answer(self):
        """Test that empty answers are rejected."""
        example = {
            "question": "What is 2+2?",
            "answer": ""
        }
        assert verify_solution_correctness(example) is False

    def test_missing_answer_key(self):
        """Test that missing 'answer' key is rejected."""
        example = {
            "question": "What is 2+2?"
        }
        assert verify_solution_correctness(example) is False

    def test_invalid_number_in_hash(self):
        """Test that NaN or invalid numbers in #### are rejected."""
        # Note: re.search might not catch 'NaN' as a float, but the float() conversion will
        example = {
            "question": "What is 2+2?",
            "answer": "The answer is NaN. #### NaN"
        }
        assert verify_solution_correctness(example) is False

    def test_extremely_large_number(self):
        """Test that extremely large numbers are rejected."""
        example = {
            "question": "What is 2+2?",
            "answer": "The answer is 1e20. #### 1e20"
        }
        # Our logic checks abs(final_value) < 1e10
        assert verify_solution_correctness(example) is False

    def test_reasoning_before_hash(self):
        """Test that reasoning text before #### is handled correctly."""
        example = {
            "question": "Complex math problem.",
            "answer": "First we do X. Then Y. Finally Z. #### 42"
        }
        assert verify_solution_correctness(example) is True