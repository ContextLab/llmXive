"""
Unit tests for feature extraction functions in code/features.py.

Specifically covers:
- T018: TTR and MTLD calculation
- T019: Syntactic complexity metrics (Clause Length, T-unit)
- T020: Semantic coherence (Sentence Embedding Cosine Similarity)
"""
import unittest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from features import (
    calculate_ttr,
    calculate_mtld,
    calculate_noun_verb_ratio,
    calculate_mean_clause_length,
    calculate_t_unit_count,
    calculate_participant_similarity,
    get_embedding_model,
    get_nlp
)
from config import set_seed

# Set seed for reproducibility in tests if needed
set_seed(42)


class TestLexicalFeatures(unittest.TestCase):
    """Tests for T018: Lexical feature extraction (TTR, MTLD, Noun/Verb ratio)."""

    def test_calculate_ttr_basic(self):
        """Test basic Type-Token Ratio calculation."""
        tokens = ["the", "cat", "sat", "on", "the", "mat"]
        ttr = calculate_ttr(tokens)
        # 6 tokens, 5 unique types (the is repeated)
        expected = 5 / 6
        self.assertAlmostEqual(ttr, expected, places=5)

    def test_calculate_ttr_empty(self):
        """Test TTR with empty list."""
        ttr = calculate_ttr([])
        self.assertEqual(ttr, 0.0)

    def test_calculate_ttr_single(self):
        """Test TTR with single token."""
        ttr = calculate_ttr(["word"])
        self.assertEqual(ttr, 1.0)

    def test_calculate_mtld_basic(self):
        """Test Measure of Textual Lexical Diversity (MTLD) with a known segment."""
        # A simple sentence with high diversity
        text = "The quick brown fox jumps over the lazy dog"
        tokens = text.lower().split()
        mtld = calculate_mtld(tokens)
        self.assertGreater(mtld, 0)
        self.assertLessEqual(mtld, 100)

    def test_calculate_mtld_empty(self):
        """Test MTLD with empty text."""
        mtld = calculate_mtld([])
        self.assertEqual(mtld, 0.0)

    def test_calculate_noun_verb_ratio_basic(self):
        """Test Noun/Verb ratio calculation."""
        # Mock tokens where we can infer POS via a simple heuristic if needed,
        # but the function should handle the spacy pipeline internally.
        # We rely on the function's internal logic here.
        text = "The cat runs fast."
        tokens = text.split()
        ratio = calculate_noun_verb_ratio(tokens)
        # We expect a non-negative number. Exact value depends on spacy parsing.
        self.assertGreaterEqual(ratio, 0.0)

    def test_calculate_noun_verb_ratio_no_verbs(self):
        """Test ratio when no verbs are detected."""
        # This depends on spacy, but we test for robustness
        text = "The cat."
        tokens = text.split()
        ratio = calculate_noun_verb_ratio(tokens)
        # If no verbs, ratio might be inf or handled. We check it runs.
        self.assertIsInstance(ratio, float)


class TestSyntacticFeatures(unittest.TestCase):
    """Tests for T019: Syntactic feature extraction (Clause Length, T-unit)."""

    @classmethod
    def setUpClass(cls):
        # Load spacy model once for tests
        cls.nlp = get_nlp()

    def test_calculate_mean_clause_length_basic(self):
        """Test mean clause length calculation."""
        text = "The cat, which is black, sat on the mat."
        tokens = text.split()
        # The function handles parsing internally
        mean_len = calculate_mean_clause_length(text)
        self.assertGreater(mean_len, 0)

    def test_calculate_mean_clause_length_empty(self):
        """Test mean clause length with empty string."""
        mean_len = calculate_mean_clause_length("")
        self.assertEqual(mean_len, 0.0)

    def test_calculate_t_unit_count_basic(self):
        """Test T-unit count calculation."""
        text = "I went to the store. I bought milk."
        count = calculate_t_unit_count(text)
        # Expect 2 T-units (two main clauses)
        self.assertEqual(count, 2)

    def test_calculate_t_unit_count_complex(self):
        """Test T-unit count with complex sentences."""
        text = "Although it was raining, we went out."
        count = calculate_t_unit_count(text)
        # 1 main clause + 1 subordinate = 1 T-unit
        self.assertEqual(count, 1)


class TestSemanticFeatures(unittest.TestCase):
    """Tests for T020: Semantic coherence (Sentence Embedding Cosine Similarity)."""

    @classmethod
    def setUpClass(cls):
        # Load embedding model once for tests
        cls.model = get_embedding_model()

    def test_calculate_participant_similarity_identical(self):
        """Test that identical sentences have similarity ~1.0."""
        sentence1 = "The cat sat on the mat."
        sentence2 = "The cat sat on the mat."
        similarity = calculate_participant_similarity([sentence1, sentence2], self.model)
        # Due to floating point, allow small epsilon
        self.assertGreater(similarity, 0.99)
        self.assertLessEqual(similarity, 1.001)

    def test_calculate_participant_similarity_different(self):
        """Test that different sentences have lower similarity."""
        sentence1 = "The cat sat on the mat."
        sentence2 = "The dog barked at the mailman."
        similarity = calculate_participant_similarity([sentence1, sentence2], self.model)
        # Should be significantly less than 1.0
        self.assertLess(similarity, 0.9)
        self.assertGreaterEqual(similarity, -1.0)

    def test_calculate_participant_similarity_single(self):
        """Test similarity with a single sentence (self-similarity)."""
        sentence1 = "The cat sat on the mat."
        similarity = calculate_participant_similarity([sentence1], self.model)
        self.assertGreater(similarity, 0.99)

    def test_calculate_participant_similarity_empty(self):
        """Test similarity with empty list."""
        similarity = calculate_participant_similarity([], self.model)
        self.assertEqual(similarity, 0.0)

    def test_calculate_participant_similarity_nan_handling(self):
        """Test that NaN inputs are handled gracefully."""
        # Simulate a case where embedding might fail (though model usually handles text)
        # We test the logic path if a vector is invalid, though the model usually raises.
        # Here we test the function's robustness with valid text that might result in low similarity.
        sentence1 = "aaaaa"
        sentence2 = "bbbbb"
        similarity = calculate_participant_similarity([sentence1, sentence2], self.model)
        self.assertIsInstance(similarity, float)
        self.assertFalse(np.isnan(similarity))


if __name__ == '__main__':
    unittest.main()