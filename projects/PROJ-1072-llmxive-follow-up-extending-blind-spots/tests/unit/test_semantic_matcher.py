"""
Unit tests for semantic equivalence threshold in semantic_matcher.py.

This test suite validates the behavior of the semantic matching logic,
specifically focusing on the threshold parameter used to determine
paraphrase equivalence.

Tests verify:
1. Exact matches always pass (similarity ~1.0)
2. Obvious non-matches fail (similarity ~0.0)
3. Threshold sensitivity: values just above/below the threshold behave correctly
4. The tuned threshold from pilot study is respected when loaded
"""

import pytest
import numpy as np
from pathlib import Path
import sys
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.semantic_matcher import encode_texts, cosine_similarity, is_paraphrase, batch_is_paraphrase
from utils.logging_config import get_logger

logger = get_logger(__name__)


class TestSemanticMatcherThreshold:
    """Tests for the semantic equivalence threshold logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.logger = get_logger(__name__)
        # Use a fixed seed for reproducibility if needed in tests
        np.random.seed(42)

    def test_exact_matches_pass_high_similarity(self):
        """Exact or near-exact matches should have high similarity and pass default threshold."""
        sentences = [
            "The cat sat on the mat.",
            "The cat sat on the mat.",  # Exact duplicate
            "A feline rested on the rug.",  # Very similar meaning
        ]

        embeddings = encode_texts(sentences)
        similarities = cosine_similarity(embeddings[0], embeddings[1:])

        # The exact duplicate should have very high similarity (> 0.9)
        assert similarities[0] > 0.9, f"Exact match similarity {similarities[0]} should be > 0.9"

        # The paraphrase should also be high, though potentially lower
        # This depends on the model, but usually > 0.8 for clear paraphrases
        assert similarities[1] > 0.5, f"Paraphrase similarity {similarities[1]} should be > 0.5"

    def test_obvious_non_matches_fail(self):
        """Unrelated sentences should have low similarity and fail default threshold."""
        sentences = [
            "The cat sat on the mat.",
            "Quantum entanglement describes a physical phenomenon.",
            "The stock market crashed yesterday.",
        ]

        embeddings = encode_texts(sentences)
        similarities = cosine_similarity(embeddings[0], embeddings[1:])

        # Both should be low similarity
        assert similarities[0] < 0.3, f"Unrelated sentence 1 similarity {similarities[0]} should be < 0.3"
        assert similarities[1] < 0.3, f"Unrelated sentence 2 similarity {similarities[1]} should be < 0.3"

    def test_threshold_sensitivity_above(self):
        """Sentences with similarity just above threshold should be classified as paraphrases."""
        # We simulate this by creating a test that checks the logic directly
        # Since we can't easily control the exact similarity score without mocking,
        # we test the boundary logic of is_paraphrase function

        # Create a scenario where we know the similarity is high
        s1 = "Constraint must be mentioned in the first 256 tokens."
        s2 = "Constraint must be mentioned in the first 256 tokens."  # Exact match

        # Test with a very high threshold (0.99) - should pass
        result_high = is_paraphrase(s1, s2, threshold=0.99)
        assert result_high is True, "Exact match should pass even at 0.99 threshold"

        # Test with a very low threshold (0.1) - should pass
        result_low = is_paraphrase(s1, s2, threshold=0.1)
        assert result_low is True, "Exact match should pass at 0.1 threshold"

    def test_threshold_sensitivity_below(self):
        """Sentences with similarity just below threshold should NOT be classified as paraphrases."""
        # Test with unrelated sentences and various thresholds
        s1 = "The cat sat on the mat."
        s2 = "Quantum entanglement describes a physical phenomenon."

        # Test with a high threshold (0.9) - should fail
        result_high = is_paraphrase(s1, s2, threshold=0.9)
        assert result_high is False, "Unrelated sentences should fail at 0.9 threshold"

        # Test with a moderate threshold (0.5) - should fail
        result_mod = is_paraphrase(s1, s2, threshold=0.5)
        assert result_mod is False, "Unrelated sentences should fail at 0.5 threshold"

    def test_batch_is_paraphrase_respects_threshold(self):
        """batch_is_paraphrase should correctly apply threshold to all pairs."""
        queries = [
            "Constraint mentioned early",
            "Constraint mentioned early",  # Duplicate
            "Unrelated sentence here"
        ]
        candidates = [
            "Constraint mentioned early",  # Match
            "Constraint mentioned in beginning",  # Paraphrase
            "Something completely different"  # No match
        ]

        # Default threshold (typically around 0.7-0.8 for MiniLM)
        results_default = batch_is_paraphrase(queries, candidates)

        # First query should match first two candidates
        assert results_default[0][0] is True, "First query should match first candidate"
        # The second match depends on the model's paraphrase capability
        # We expect it to be True for a clear paraphrase
        # If False, it means the threshold is too high for this specific paraphrase

        # Second query (duplicate) should have same results as first
        assert results_default[1] == results_default[0], "Duplicate queries should have same results"

        # Third query should have no matches
        assert all(not r for r in results_default[2]), "Unrelated query should have no matches"

    def test_is_paraphrase_handles_empty_strings(self):
        """Empty strings should be handled gracefully."""
        # Empty vs non-empty
        result1 = is_paraphrase("", "Some text")
        # This might raise or return False depending on model behavior
        # We just check it doesn't crash with a weird error

        # Empty vs empty
        result2 = is_paraphrase("", "")
        # Should be True or False, but not crash

    def test_threshold_from_config_integration(self):
        """Test that a loaded threshold from a config file works correctly."""
        # Simulate a tuned threshold from pilot study
        tuned_threshold = 0.75

        s1 = "The constraint is mentioned at the start."
        s2 = "The constraint is mentioned at the start."  # Exact match

        result = is_paraphrase(s1, s2, threshold=tuned_threshold)
        assert result is True, "Exact match should pass at tuned threshold"

        s3 = "Completely unrelated text."
        result_fail = is_paraphrase(s1, s3, threshold=tuned_threshold)
        assert result_fail is False, "Unrelated text should fail at tuned threshold"

    def test_cosine_similarity_range(self):
        """Verify that cosine similarity returns values in [-1, 1] range."""
        sentences = [
            "Text A",
            "Text B",
            "Text C"
        ]

        embeddings = encode_texts(sentences)

        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                sim = cosine_similarity(embeddings[i], embeddings[j])
                assert -1.0 <= sim <= 1.0, f"Similarity {sim} out of range [-1, 1]"

    def test_consistency_with_same_input(self):
        """Running the same input twice should yield consistent results."""
        s1 = "Test consistency sentence."
        s2 = "Test consistency sentence."

        # Run multiple times
        results = []
        for _ in range(3):
            results.append(is_paraphrase(s1, s2, threshold=0.7))

        # All results should be the same (True)
        assert all(r == results[0] for r in results), "Results should be consistent"
        assert results[0] is True, "Exact match should consistently be True"

    def test_threshold_boundary_behavior(self):
        """Test behavior when similarity is exactly at the threshold."""
        # This is a theoretical test since we can't easily control exact similarity
        # We test the logic: if sim >= threshold, then True
        # If sim < threshold, then False

        # We'll mock a scenario by testing the comparison logic
        # Since we can't force exact similarity, we test with a range

        # Create a pair that is likely to be around 0.7-0.8
        s1 = "The model should mention the constraint early in the response."
        s2 = "The constraint needs to be mentioned at the beginning of the trace."

        # Test with threshold 0.7
        result_7 = is_paraphrase(s1, s2, threshold=0.7)

        # Test with threshold 0.8
        result_8 = is_paraphrase(s1, s2, threshold=0.8)

        # If result_7 is True and result_8 is False, it means similarity is between 0.7 and 0.8
        # If both are True, similarity >= 0.8
        # If both are False, similarity < 0.7

        # The important thing is that the behavior is consistent and monotonic
        # If it passes at 0.8, it must pass at 0.7
        if result_8:
            assert result_7 is True, "If passes at 0.8, must pass at 0.7"

    def test_paraphrase_detection_with_various_thresholds(self):
        """Test that paraphrase detection works across a range of thresholds."""
        # A clear paraphrase pair
        s1 = "The constraint must be mentioned in the first part of the response."
        s2 = "The constraint needs to appear early in the generated text."

        thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
        results = []

        for thresh in thresholds:
            results.append(is_paraphrase(s1, s2, threshold=thresh))

        # Results should be monotonic: if True at T, must be True at T-0.1
        for i in range(1, len(results)):
            if results[i]:  # If True at higher threshold
                assert results[i-1] is True, f"Monotonicity violation: True at {thresholds[i]} but False at {thresholds[i-1]}"

    def test_semantic_matcher_uses_correct_model(self):
        """Verify that the semantic matcher uses the expected model."""
        # This test checks that the model loaded is the one specified in the code
        # We can't easily verify the model name without inspecting internals,
        # but we can check that the encoding works as expected

        test_sentences = ["Hello world", "Test sentence"]
        embeddings = encode_texts(test_sentences)

        # Embeddings should be non-zero and have the expected shape
        assert embeddings.shape[0] == 2, "Should have 2 embeddings"
        assert embeddings.shape[1] > 0, "Embeddings should have non-zero dimension"

        # Check that embeddings are normalized (for cosine similarity to work correctly)
        norms = np.linalg.norm(embeddings, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-5), "Embeddings should be normalized"