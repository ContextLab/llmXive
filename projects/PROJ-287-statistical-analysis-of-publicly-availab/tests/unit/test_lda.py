import unittest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.models.lda.k_selector import select_optimal_k, compute_elbow_metric


class TestLdaKSelection(unittest.TestCase):
    """Unit tests for k-selection logic (elbow method within 10% tolerance)."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_docs = [
            "document one words here",
            "document two words here",
            "document three words here",
            "document four words here",
            "document five words here",
        ]
        self.mock_vocabulary = ["document", "one", "two", "three", "words", "here"]
        self.mock_term_document_matrix = np.random.rand(5, 5).astype(np.float32)

    @patch('src.models.lda.k_selector.LdaModel')
    def test_elbow_method_selects_k10_within_tolerance(self, mock_lda_class):
        """
        Test that the elbow method identifies k=10 as optimal within 10% tolerance.
        
        Simulates a scenario where k=10 provides the best balance between 
        reconstruction error and model complexity (the "elbow").
        """
        # Mock LdaModel instances to return decreasing inertia scores
        mock_instances = []
        inertias = [1000.0, 800.0, 650.0, 550.0, 480.0, 430.0, 390.0, 360.0, 340.0, 330.0]
        
        for inertia in inertias:
            mock_lda = MagicMock()
            mock_lda.inertia_ = inertia
            mock_instances.append(mock_lda)
        
        mock_lda_class.side_effect = mock_instances

        # Run k-selection with range including 10
        optimal_k = select_optimal_k(
            self.mock_term_document_matrix,
            k_range=range(5, 16),
            max_iter=10
        )

        # Verify k=10 is selected (the elbow point in our mock data)
        self.assertEqual(optimal_k, 10)

    @patch('src.models.lda.k_selector.LdaModel')
    def test_elbow_tolerance_accepts_nearby_k(self, mock_lda_class):
        """
        Test that the algorithm accepts k values within 10% tolerance of the true elbow.
        
        If the true elbow is at k=10, then k=9 or k=11 should be acceptable
        if the improvement curve flattens significantly there.
        """
        # Create a scenario where the elbow is less sharp, making 9 or 11 acceptable
        mock_instances = []
        # Flatter curve around k=10
        inertias = [1000.0, 900.0, 820.0, 750.0, 690.0, 640.0, 600.0, 570.0, 550.0, 540.0, 535.0]
        
        for inertia in inertias:
            mock_lda = MagicMock()
            mock_lda.inertia_ = inertia
            mock_instances.append(mock_lda)
        
        mock_lda_class.side_effect = mock_instances

        optimal_k = select_optimal_k(
            self.mock_term_document_matrix,
            k_range=range(5, 16),
            max_iter=10
        )

        # The result should be within 10% of the expected elbow (k=10)
        # 10% of 10 is 1, so acceptable range is [9, 11]
        self.assertIn(optimal_k, [9, 10, 11])

    @patch('src.models.lda.k_selector.LdaModel')
    def test_k_selection_fails_gracefully_with_insufficient_data(self, mock_lda_class):
        """
        Test that the function handles cases where the elbow is not detectable.
        
        If the inertia curve is linear or noisy, the algorithm should still
        return a valid k within the provided range.
        """
        # Mock linear inertia decrease (no clear elbow)
        mock_instances = []
        inertias = [1000.0, 900.0, 800.0, 700.0, 600.0, 500.0, 400.0, 300.0, 200.0, 100.0]
        
        for inertia in inertias:
            mock_lda = MagicMock()
            mock_lda.inertia_ = inertia
            mock_instances.append(mock_lda)
        
        mock_lda_class.side_effect = mock_instances

        # Should not raise an exception
        optimal_k = select_optimal_k(
            self.mock_term_document_matrix,
            k_range=range(5, 11),
            max_iter=10
        )

        # Should return the maximum k when no elbow is found (conservative approach)
        self.assertEqual(optimal_k, 10)

    def test_compute_elbow_metric_returns_valid_scores(self):
        """
        Test that the elbow metric computation returns valid numeric scores.
        """
        inertias = [1000.0, 800.0, 650.0, 550.0, 480.0]
        k_values = list(range(5, 10))
        
        scores = compute_elbow_metric(inertias, k_values)
        
        # Scores should be non-negative
        self.assertTrue(all(s >= 0 for s in scores))
        
        # Scores should correspond to the number of k values minus 2 (first two points have no previous)
        self.assertEqual(len(scores), len(k_values) - 2)

    @patch('src.models.lda.k_selector.LdaModel')
    def test_k_selection_respects_max_k_limit(self, mock_lda_class):
        """
        Test that the algorithm does not exceed the specified maximum k.
        """
        mock_instances = []
        inertias = [1000.0, 800.0, 650.0, 550.0, 480.0, 430.0, 390.0, 360.0, 340.0, 330.0]
        
        for inertia in inertias:
            mock_lda = MagicMock()
            mock_lda.inertia_ = inertia
            mock_instances.append(mock_lda)
        
        mock_lda_class.side_effect = mock_instances

        # Limit k_range to 5-8
        optimal_k = select_optimal_k(
            self.mock_term_document_matrix,
            k_range=range(5, 9),
            max_iter=10
        )

        # Result should be within the specified range
        self.assertGreaterEqual(optimal_k, 5)
        self.assertLessEqual(optimal_k, 8)


if __name__ == '__main__':
    unittest.main()