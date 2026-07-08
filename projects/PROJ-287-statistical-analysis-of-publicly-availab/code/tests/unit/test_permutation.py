import unittest
import tempfile
import json
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.models.metrics.permutation import stratified_sample_by_window, run_permutation_test

class TestPermutationLogic(unittest.TestCase):

    def setUp(self):
        self.sample_data = [
            {"window": "2000-2004", "tokens": ["word1", "word2"]},
            {"window": "2000-2004", "tokens": ["word3", "word4"]},
            {"window": "2005-2009", "tokens": ["word5", "word6"]},
            {"window": "2005-2009", "tokens": ["word7", "word8"]},
            {"window": "2010-2014", "tokens": ["word9", "word10"]},
        ]

    def test_stratified_sample_small_dataset(self):
        # If total < min_samples, return all
        result = stratified_sample_by_window(self.sample_data, min_samples=2000)
        self.assertEqual(len(result), len(self.sample_data))

    def test_stratified_sample_large_dataset(self):
        # Create a larger dataset
        large_data = []
        for i in range(3000):
            large_data.append({"window": "2000-2004", "tokens": ["w"]})
        for i in range(1000):
            large_data.append({"window": "2005-2009", "tokens": ["w"]})
        
        result = stratified_sample_by_window(large_data, min_samples=2000)
        self.assertLessEqual(len(result), 2000)
        # Check representation
        windows = [r["window"] for r in result]
        self.assertIn("2000-2004", windows)
        self.assertIn("2005-2009", windows)

    @patch('src.models.metrics.permutation.fit_lda_model')
    @patch('src.models.metrics.permutation.TopicAligner')
    def test_run_permutation_test_mocked(self, mock_aligner_class, mock_fit):
        # Mock the heavy lifting to test logic flow
        mock_aligner = MagicMock()
        mock_aligner_class.return_value = mock_aligner
        
        # Mock LDA fit to return dummy components
        mock_lda = MagicMock()
        mock_lda.components_ = np.random.rand(10, 100)
        mock_fit.return_value = mock_lda

        # Mock vectorizer
        with patch('src.models.metrics.permutation.CountVectorizer') as mock_vec_class:
            mock_vec = MagicMock()
            mock_vec.transform.return_value = np.random.rand(10, 100)
            mock_vec.fit_transform.return_value = np.random.rand(10, 100)
            mock_vec_class.return_value = mock_vec

            # Mock alignment to return a dict
            mock_aligner.align_matrices.return_value = {
                "2000-2004": np.random.rand(10, 100),
                "2005-2009": np.random.rand(10, 100)
            }

            # Run with very small n_permutations for speed
            result = run_permutation_test(
                tokenized_data=self.sample_data,
                window_col="window",
                text_col="tokens",
                n_permutations=5,
                n_topics=10,
                max_iter=2
            )

            self.assertIn("observed_divergences", result)
            self.assertIn("p_values", result)
            self.assertIn("null_distributions", result)
            self.assertEqual(result["n_permutations"], 5)
            self.assertIsInstance(result["p_values"], list)

if __name__ == "__main__":
    unittest.main()
