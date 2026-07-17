import pytest
import sys
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.download_gsm8k import verify_solution_correctness

class TestGSM8KFiltering:
    """Unit tests for GSM8K filtering logic."""

    def test_valid_solution_format(self):
        """Test that a correctly formatted solution returns True."""
        solution = "If John has 5 apples and gives 2 away, he has 3 left. #### 3"
        # Note: The verify function in download_gsm8k parses the solution itself.
        # This test checks the internal logic of verification against the solution string.
        # Since the function signature in download_gsm8k is verify_solution_correctness(solution, answer),
        # and the dataset provides 'answer' as the solution string, we simulate a check.
        # However, the current implementation of verify_solution_correctness in download_gsm8k
        # expects (solution_text, answer_text) where answer_text is the ground truth.
        # In the GSM8K dataset, the 'answer' field IS the solution.
        # To test this properly, we mock the scenario where we extract the truth from the solution.
        
        # Let's test the logic directly:
        # If the solution ends with #### 3, and we pass "#### 3" as the answer text.
        assert verify_solution_correctness(solution, "#### 3") is True

    def test_mismatched_solution(self):
        """Test that a solution with a different final answer returns False."""
        solution = "The result is 10. #### 10"
        assert verify_solution_correctness(solution, "#### 20") is False

    def test_missing_answer_marker(self):
        """Test that a solution without #### returns False."""
        solution = "The answer is 5."
        assert verify_solution_correctness(solution, "#### 5") is False

    def test_empty_inputs(self):
        """Test handling of empty inputs."""
        assert verify_solution_correctness("", "#### 5") is False
        assert verify_solution_correctness("Some text", "") is False
        assert verify_solution_correctness("", "") is False

    def test_complex_numbers(self):
        """Test parsing of complex numbers with commas."""
        solution = "The total cost is 1,200. #### 1,200"
        assert verify_solution_correctness(solution, "#### 1,200") is True

    def test_floating_point_tolerance(self):
        """Test floating point comparison tolerance."""
        solution = "The result is 3.14159. #### 3.14159"
        assert verify_solution_correctness(solution, "#### 3.14159") is True
