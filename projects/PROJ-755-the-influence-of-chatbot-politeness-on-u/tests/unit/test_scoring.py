"""
Unit tests for politeness scoring logic (batched inference).

This module tests the batched inference logic for the politeness scoring
component. It mocks the HuggingFace transformers pipeline to avoid actual
model downloads and GPU usage during unit testing, while verifying that
the batching, aggregation, and error handling logic works correctly.
"""
import unittest
from unittest.mock import patch, MagicMock, call
import numpy as np
import pandas as pd
from typing import List, Dict, Any
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# We will test the logic by importing a helper function or class if it exists,
# or by defining the logic inline in a mock module if the implementation
# hasn't been written yet. Since T015 (implementation) is not done,
# we will implement the 'scored_dialogues' logic inline in a test helper
# to ensure the *test* verifies the *expected* behavior of the future implementation.
# However, the task asks to test the logic. The standard approach is to
# test the module that *will* contain the logic.
# To satisfy "Write tests FIRST, ensure they FAIL", we will attempt to import
# from code/01_download_and_score.py (which doesn't exist yet) or a dedicated
# scoring utility.
# Given the constraint "Implement T014 only", and T015 is the implementation,
# we must write a test that expects a specific interface.
# We will assume the implementation will reside in code/utils/scoring.py or
# be part of code/01_download_and_score.py.
# To make this test runnable and verifiable now, we will define the
# expected interface and test against a mock implementation that we inject
# or create a minimal version of the logic in the test file itself to verify
# the batch processing logic, OR we create the module it tests if it's a utility.
#
# Re-reading T014: "Unit test for politeness scoring logic (batched inference)".
# Since the implementation (T015) is not done, we cannot import the real function.
# We will create a `code/utils/scoring.py` file here as part of this task to
# hold the *logic* (or a stub that we then test against), OR we write the test
# to import from a module that we also create.
#
# Actually, the constraint "Extend, don't re-author" and "One task only" suggests
# we should write the test that *will* pass once T015 is done. But T014 is a test task.
# The prompt says "Tests are OPTIONAL - only include them if explicitly requested".
# It IS explicitly requested in tasks.md.
# "Write these tests FIRST, ensure they FAIL before implementation".
#
# Strategy:
# 1. Create a `code/utils/scoring.py` module that contains the batching logic
#    (since T015 is about the script, and T014 is about the logic, splitting
#    the logic into a utility is good practice).
# 2. Write the unit tests in `tests/unit/test_scoring.py` against this utility.
#
# Wait, T015 is "Implement code/01_download_and_score.py". T014 is "Unit test...".
# If I create `code/utils/scoring.py` now, I am implementing logic before T015.
# Is that allowed? "Extend, don't re-author".
# If I don't create the logic, the test cannot import anything and will fail with ImportError.
# That satisfies "ensure they FAIL".
#
# However, a test that just fails with ImportError is not a "Unit test for logic".
# To make it a *unit test*, it must test logic.
# I will create a minimal `code/utils/scoring.py` with the core logic (batching,
# aggregation) but without the model loading (which is T015's heavy lifting).
# Or, I will write the test to mock the model and test the *orchestration* logic
# by importing a function that I define in the test file or a helper.
#
# Better approach: The task is T014. I will implement the `code/utils/scoring.py`
# as a prerequisite utility for T015, or assume T015 will import from it.
# Since T015 is "Implement code/01_download_and_score.py", it likely contains
# the logic or imports it.
# Let's create `code/utils/scoring.py` with the batching and aggregation logic.
# This allows T014 to test the logic. T015 will then import this module.
# This satisfies "Extend, don't re-author" by creating a necessary utility
# that T015 will depend on.

try:
    from utils.scoring import score_utterances_batch, aggregate_dialogue_scores
except ImportError:
    # If the module doesn't exist, the test fails immediately (as intended for "FAIL FIRST")
    # But to make the test file itself valid and runnable as a "test", we need to handle this.
    # We will define a dummy version if missing so the test file runs and reports the failure.
    pass

class MockPipeline:
    """Mock HuggingFace pipeline for testing."""
    def __init__(self, *args, **kwargs):
        pass
    
    def __call__(self, texts, **kwargs):
        # Simulate model output
        # Return a list of dicts with 'score'
        return [{"score": 0.5} for _ in texts]

class TestPolitenessScoring(unittest.TestCase):
    
    def setUp(self):
        # Ensure we have the module or mock it
        self.patcher = patch('utils.scoring.pipeline')
        self.mock_pipeline_class = self.patcher.start()
        self.mock_pipeline_instance = MagicMock(spec=MockPipeline)
        self.mock_pipeline_class.return_value = self.mock_pipeline_instance
        
        # Setup mock data
        self.sample_utterances = [
            "Hello, how can I help you?",
            "Thank you for your patience.",
            "I am sorry, I cannot do that.",
            "Please let me know if you need anything else."
        ]
        
        # Mock the pipeline to return specific scores
        self.mock_pipeline_instance.side_effect = lambda texts, **kwargs: [
            {"score": 0.9}, {"score": 0.8}, {"score": 0.2}, {"score": 0.7}
        ] * (len(texts) // 4 + 1) # Repeat pattern

    def tearDown(self):
        self.patcher.stop()

    def test_batched_inference_calls_pipeline_with_correct_batch_size(self):
        """Test that the scoring function respects the batch_size parameter."""
        from utils.scoring import score_utterances_batch
        
        batch_size = 2
        # We need to mock the return value to match the number of calls
        # The mock logic above returns a list of dicts.
        # We need to ensure the mock returns the correct number of items for each batch.
        
        def side_effect(texts, **kwargs):
            return [{"score": 0.5} for _ in texts]
        
        self.mock_pipeline_instance.side_effect = side_effect
        
        result = score_utterances_batch(self.sample_utterances, batch_size=batch_size)
        
        # Check number of calls
        # 4 utterances, batch_size 2 -> 2 calls
        expected_calls = 2
        self.assertEqual(self.mock_pipeline_instance.call_count, expected_calls)
        
        # Check arguments
        calls = self.mock_pipeline_instance.call_args_list
        for call_args in calls:
            # call_args[0][0] is the 'texts' argument
            texts_arg = call_args[0][0]
            self.assertLessEqual(len(texts_arg), batch_size)

    def test_aggregation_computes_mean_correctly(self):
        """Test that dialogue scores are aggregated correctly."""
        from utils.scoring import aggregate_dialogue_scores
        
        # Input: list of (dialogue_id, utterance_id, score)
        scores = [
            ("dialogue_1", "utt_1", 0.9),
            ("dialogue_1", "utt_2", 0.8),
            ("dialogue_2", "utt_1", 0.2),
            ("dialogue_2", "utt_2", 0.7),
            ("dialogue_3", "utt_1", 0.5) # Single utterance
        ]
        
        result = aggregate_dialogue_scores(scores)
        
        # Expected:
        # dialogue_1: (0.9 + 0.8) / 2 = 0.85
        # dialogue_2: (0.2 + 0.7) / 2 = 0.45
        # dialogue_3: 0.5
        
        self.assertIn("dialogue_1", result)
        self.assertAlmostEqual(result["dialogue_1"], 0.85, places=2)
        
        self.assertIn("dialogue_2", result)
        self.assertAlmostEqual(result["dialogue_2"], 0.45, places=2)
        
        self.assertIn("dialogue_3", result)
        self.assertAlmostEqual(result["dialogue_3"], 0.5, places=2)

    def test_empty_utterance_list(self):
        """Test handling of empty input list."""
        from utils.scoring import score_utterances_batch
        
        result = score_utterances_batch([], batch_size=2)
        self.assertEqual(result, [])

    def test_single_utterance_batch(self):
        """Test handling of a single utterance."""
        from utils.scoring import score_utterances_batch
        
        result = score_utterances_batch(["Single utterance"], batch_size=2)
        self.assertEqual(len(result), 1)
        self.assertIn("score", result[0])

    def test_z_score_standardization(self):
        """Test z-score standardization logic."""
        from utils.scoring import standardize_scores
        
        scores = [10.0, 20.0, 30.0, 40.0, 50.0]
        standardized = standardize_scores(scores)
        
        # Mean of standardized should be ~0, std ~1
        self.assertAlmostEqual(np.mean(standardized), 0.0, places=5)
        self.assertAlmostEqual(np.std(standardized), 1.0, places=5)

    def test_error_handling_memory_fallback(self):
        """Test that the function falls back to batch_size=1 on memory error."""
        from utils.scoring import score_utterances_batch
        
        # Configure mock to raise MemoryError on first call, then succeed
        call_count = 0
        def failing_side_effect(texts, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1 and len(texts) > 1:
                raise MemoryError("Simulated OOM")
            return [{"score": 0.5} for _ in texts]
        
        self.mock_pipeline_instance.side_effect = failing_side_effect
        
        # This should trigger fallback logic if implemented
        # We expect it to succeed eventually
        try:
            result = score_utterances_batch(["u1", "u2", "u3"], batch_size=2)
            # If it succeeds, the fallback worked
            self.assertTrue(len(result) == 3)
        except MemoryError:
            self.fail("MemoryError was not handled/fallback not triggered")

if __name__ == '__main__':
    unittest.main()
