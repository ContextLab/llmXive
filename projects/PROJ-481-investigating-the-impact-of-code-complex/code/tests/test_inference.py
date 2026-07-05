"""
Unit tests for hallucination detection and score assignment in the inference pipeline.

This module tests the `detect_hallucination` function from `code/utils/inference.py`
to ensure that non-code outputs are correctly identified and assigned a score of 0.

Test Cases:
1. Valid code output: Should return score > 0 and hallucination_flag = False.
2. Hallucinated text (non-code): Should return score = 0 and hallucination_flag = True.
3. Empty output: Should return score = 0 and hallucination_flag = True.
4. Gibberish output: Should return score = 0 and hallucination_flag = True.
"""
import sys
import os
import unittest
from pathlib import Path

# Add the project root to the path to allow imports of sibling modules
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.inference import detect_hallucination


class TestHallucinationDetection(unittest.TestCase):
    """Test suite for hallucination detection logic."""

    def test_valid_code_returns_positive_score(self):
        """
        Test that valid Python code is recognized as non-hallucinated
        and receives a positive score.
        """
        valid_code = """
        def add(a, b):
            return a + b
        """
        score, is_hallucination = detect_hallucination(valid_code)
        
        self.assertFalse(is_hallucination, "Valid code should not be flagged as hallucination")
        self.assertGreater(score, 0, "Valid code should receive a positive score")

    def test_hallucinated_text_returns_zero_score(self):
        """
        Test that non-code text (hallucination) is detected and assigned score 0.
        """
        hallucinated_text = """
        The quick brown fox jumps over the lazy dog. 
        This is not code but natural language text.
        """
        score, is_hallucination = detect_hallucination(hallucinated_text)
        
        self.assertTrue(is_hallucination, "Non-code text should be flagged as hallucination")
        self.assertEqual(score, 0, "Hallucinated text should receive a score of 0")

    def test_empty_output_returns_zero_score(self):
        """
        Test that empty output is treated as hallucination with score 0.
        """
        empty_output = ""
        score, is_hallucination = detect_hallucination(empty_output)
        
        self.assertTrue(is_hallucination, "Empty output should be flagged as hallucination")
        self.assertEqual(score, 0, "Empty output should receive a score of 0")

    def test_gibberish_returns_zero_score(self):
        """
        Test that gibberish strings are detected as hallucinations.
        """
        gibberish = "asdkfj;alksdjf;laksjdf;lkjasd;fklj"
        score, is_hallucination = detect_hallucination(gibberish)
        
        self.assertTrue(is_hallucination, "Gibberish should be flagged as hallucination")
        self.assertEqual(score, 0, "Gibberish should receive a score of 0")

    def test_mixed_content_valid_code(self):
        """
        Test that output containing valid code structure is not flagged.
        """
        mixed_code = """
        import os
        def hello():
            print("Hello World")
        """
        score, is_hallucination = detect_hallucination(mixed_code)
        
        self.assertFalse(is_hallucination, "Mixed valid code should not be flagged")
        self.assertGreater(score, 0, "Mixed valid code should receive a positive score")

    def test_mixed_content_non_code(self):
        """
        Test that output that is mostly non-code is flagged.
        """
        mixed_non_code = """
        Here is the code you asked for:
        I am an AI assistant.
        """
        score, is_hallucination = detect_hallucination(mixed_non_code)
        
        self.assertTrue(is_hallucination, "Non-code text with intro should be flagged")
        self.assertEqual(score, 0, "Non-code text should receive a score of 0")


if __name__ == '__main__':
    unittest.main()