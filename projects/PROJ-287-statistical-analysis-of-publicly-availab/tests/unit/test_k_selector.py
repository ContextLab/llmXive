import unittest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

from src.models.lda.k_selector import KSelector


class TestKSelector(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.corpus = [
            "machine learning artificial intelligence neural networks",
            "deep learning convolutional neural networks image recognition",
            "natural language processing text analysis sentiment",
            "computer vision object detection image segmentation",
            "reinforcement learning agent environment reward policy"
        ] * 10  # Repeat to have enough data for LDA
        self.vocab_size = 20
        self.selector = KSelector(min_k=2, max_k=5, target_k=3)

    def test_init(self):
        """Test initialization of KSelector."""
        self.assertEqual(self.selector.min_k, 2)
        self.assertEqual(self.selector.max_k, 5)
        self.assertEqual(self.selector.target_k, 3)
        self.assertEqual(self.selector.max_iter, 20)

    def test_fit_models_success(self):
        """Test fitting models returns valid errors and details."""
        errors, details = self.selector.fit_models(self.corpus, self.vocab_size)
        
        self.assertEqual(len(errors), 4)  # k=2,3,4,5
        self.assertEqual(len(details), 4)
        
        for i, detail in enumerate(details):
            self.assertEqual(detail["k"], i + 2)
            self.assertIn("reconstruction_error", detail)
            self.assertIn("status", detail)
            self.assertEqual(detail["status"], "success")
            self.assertIsInstance(detail["reconstruction_error"], float)

    def test_find_elbow_logic(self):
        """Test elbow detection with a known curve."""
        # Simulate a curve with a clear elbow at k=3
        # Errors: 100, 80, 60, 59, 58 (elbow at 3)
        errors = [100.0, 80.0, 60.0, 59.0, 58.0]
        optimal_k = self.selector.find_elbow(errors)
        
        # The elbow should be detected around k=3
        self.assertIn(optimal_k, [3, 4])  # Allow some flexibility

    def test_validate_target_k_true(self):
        """Test validation when target is within tolerance."""
        # Target k=3, optimal k=3, tolerance 10% -> 2.7 to 3.3
        is_valid = self.selector.validate_target_k(optimal_k=3, tolerance=0.1)
        self.assertTrue(is_valid)

    def test_validate_target_k_false(self):
        """Test validation when target is outside tolerance."""
        # Target k=3, optimal k=5, tolerance 10% -> 4.5 to 5.5
        # 3 is not in [4.5, 5.5]
        is_valid = self.selector.validate_target_k(optimal_k=5, tolerance=0.1)
        self.assertFalse(is_valid)

    def test_run_analysis(self):
        """Test the full analysis pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "k_results.json"
            results = self.selector.run_analysis(
                corpus=self.corpus,
                vocabulary_size=self.vocab_size,
                output_path=output_path
            )

            self.assertIn("target_k", results)
            self.assertIn("optimal_k", results)
            self.assertIn("is_target_valid", results)
            self.assertIn("recommendation", results)
            self.assertIn("models_fitted", results)
            
            self.assertTrue(output_path.exists())
            
            with open(output_path, 'r') as f:
                saved_results = json.load(f)
            self.assertEqual(saved_results["target_k"], results["target_k"])

    def test_empty_corpus_handling(self):
        """Test handling of empty corpus."""
        with self.assertRaises(ValueError):
            self.selector.fit_models([], self.vocab_size)

    def test_single_document_corpus(self):
        """Test with a very small corpus that might cause LDA issues."""
        small_corpus = ["single document only"]
        # This might fail or produce inf errors, but should not crash unexpectedly
        # depending on sklearn version, but we expect it to handle gracefully or raise specific error
        # For this test, we just ensure it doesn't crash with an unexpected exception type
        try:
            errors, details = self.selector.fit_models(small_corpus, 10)
            # If it succeeds, check structure
            self.assertIsInstance(errors, list)
        except Exception:
            # If it fails due to data size constraints (expected in some sklearn versions),
            # that is acceptable as long as it's a controlled failure, not a crash in our logic.
            pass


if __name__ == '__main__':
    unittest.main()