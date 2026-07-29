"""
Unit tests for the External Invariant Check (T052b).

Tests verify that the `enforce_invariant` function correctly raises
`SecurityViolation` when benchmark data is present in the prompt context.
"""

import unittest
from unittest.mock import MagicMock
from pipeline.verification import enforce_invariant, SecurityViolation, validate_prompt_context_safety

class TestInvariantEnforcement(unittest.TestCase):

    def test_no_benchmark_data(self):
        """Test that a clean context passes without error."""
        context = {
            "system_prompt": "You are a helpful assistant.",
            "user_message": "Propose an architectural change to the model.",
            "history": [
                {"role": "user", "content": "Make it faster."},
                {"role": "assistant", "content": "I will add more layers."}
            ]
        }
        # Should not raise
        enforce_invariant(context)
        self.assertTrue(validate_prompt_context_safety(context))

    def test_gsm8k_detected_string(self):
        """Test detection of 'gsm8k' in a string value."""
        context = {
            "prompt": "Evaluate performance on gsm8k dataset."
        }
        with self.assertRaises(SecurityViolation) as cm:
            enforce_invariant(context)
        self.assertIn("Benchmark data detected", str(cm.exception))
        self.assertFalse(validate_prompt_context_safety(context))

    def test_arc_challenge_detected(self):
        """Test detection of 'arc-challenge' in nested structure."""
        context = {
            "evaluation_config": {
                "benchmarks": ["wikitext-2", "arc-challenge"]
            }
        }
        with self.assertRaises(SecurityViolation) as cm:
            enforce_invariant(context)
        self.assertIn("Benchmark data detected", str(cm.exception))

    def test_wikitext_detected(self):
        """Test detection of 'wikitext' variations."""
        context = {
            "data_source": "wikitext2"
        }
        with self.assertRaises(SecurityViolation) as cm:
            enforce_invariant(context)
        self.assertIn("Benchmark data detected", str(cm.exception))

    def test_grade_school_math_detected(self):
        """Test detection of descriptive benchmark phrases."""
        context = {
            "task_description": "Solve grade school math problems."
        }
        with self.assertRaises(SecurityViolation) as cm:
            enforce_invariant(context)
        self.assertIn("Benchmark data detected", str(cm.exception))

    def test_case_insensitive(self):
        """Test that detection is case-insensitive."""
        context = {
            "note": "GSM8K results are pending."
        }
        with self.assertRaises(SecurityViolation) as cm:
            enforce_invariant(context)
        self.assertIn("Benchmark data detected", str(cm.exception))

    def test_mock_generative_call_with_benchmark(self):
        """
        Mock a generative call containing benchmark data and assert SecurityViolation.
        This simulates the scenario where the generative model accidentally
        includes benchmark data in its context window.
        """
        # Simulate a complex context that might be passed to a generative model
        mock_context = {
            "system_instruction": "You are a self-improving AI.",
            "current_state": {
                "loss": 0.45,
                "accuracy": 0.72
            },
            "context_window": [
                {
                    "role": "user",
                    "content": "Here is the GSM8K test set for you to analyze: [data...]"
                },
                {
                    "role": "assistant",
                    "content": "I will analyze the data."
                }
            ],
            "metadata": {
                "benchmark": "arc-challenge",
                "version": "1.0"
            }
        }

        with self.assertRaises(SecurityViolation) as cm:
            enforce_invariant(mock_context)

        # Verify the error message contains relevant details
        error_msg = str(cm.exception)
        self.assertIn("Benchmark data detected", error_msg)
        self.assertIn("prompt context", error_msg)

    def test_safe_context_with_similar_words(self):
        """Test that words containing substrings but not full matches pass."""
        # 'arc' is a common word, but 'arc-challenge' is the keyword.
        # Our regex uses word boundaries, so 'arc' alone should be safe if not in the list.
        # 'arc' is in the list as a keyword, but let's test 'architectural' which contains 'arc'.
        context = {
            "prompt": "Change the architectural structure of the network."
        }
        # 'architectural' contains 'arc' but is a different word.
        # Our regex uses \b (word boundary), so it should NOT match 'architectural' as 'arc'.
        # However, 'arc' is in BENCHMARK_KEYWORDS. Let's check the regex logic.
        # The regex is \b(arc|...)\b. 'architectural' starts with 'arc' but is not 'arc'.
        # So this should pass.
        enforce_invariant(context) # Should not raise

    def test_empty_context(self):
        """Test that an empty context passes."""
        context = {}
        enforce_invariant(context)
        self.assertTrue(validate_prompt_context_safety(context))

if __name__ == '__main__':
    unittest.main()