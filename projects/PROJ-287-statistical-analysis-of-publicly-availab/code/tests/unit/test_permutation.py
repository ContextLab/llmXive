import unittest
import tempfile
import json
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add code to path if needed
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.models.metrics.permutation import stratified_sample_by_window, run_permutation_test
from src.models.entities import TopicVector

class TestPermutationLogic(unittest.TestCase):

    def test_stratified_sample_by_window(self):
        """Test that stratified sampling respects the min(2000, available) limit."""
        # Create mock data
        data = []
        windows = ["w1", "w2", "w3"]
        counts = [100, 3000, 500] # w2 has >2000, others <2000

        for i, w in enumerate(windows):
            for j in range(counts[i]):
                data.append({"window": w, "tokens": ["word"] * 20})

        sampled = stratified_sample_by_window(data, windows, max_per_window=2000, random_seed=42)

        # Check counts
        sampled_counts = {}
        for item in sampled:
            w = item["window"]
            sampled_counts[w] = sampled_counts.get(w, 0) + 1

        self.assertEqual(sampled_counts["w1"], 100)
        self.assertEqual(sampled_counts["w2"], 2000)
        self.assertEqual(sampled_counts["w3"], 500)
        self.assertEqual(len(sampled), 2600)

    def test_run_permutation_test_structure(self):
        """Test the structure of the output from run_permutation_test."""
        # Mock dependencies to avoid heavy computation
        with patch('src.models.metrics.permutation.load_preprocessed_data') as mock_load, \
             patch('src.models.metrics.permutation.fit_lda_model') as mock_fit, \
             patch('src.models.metrics.permutation.TopicAligner') as mock_aligner_class:

            # Setup mock data
            mock_data = [
                {"window": "2000-2004", "tokens": ["a", "b", "c"] * 20},
                {"window": "2005-2009", "tokens": ["d", "e", "f"] * 20}
            ]
            mock_load.return_value = mock_data

            # Setup mock LDA result
            mock_topic_vector = MagicMock(spec=TopicVector)
            mock_topic_vector.distribution = np.array([0.5, 0.5])
            mock_fit.return_value = mock_topic_vector

            # Setup mock aligner
            mock_aligner = MagicMock()
            mock_aligner.align.return_value = {"2000-2004": mock_topic_vector, "2005-2009": mock_topic_vector}
            mock_aligner_class.return_value = mock_aligner

            # Run test with n_permutations=2 for speed
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "results.json"
                result = run_permutation_test(
                    processed_data_path=Path("dummy.csv"),
                    windows=["2000-2004", "2005-2009"],
                    n_permutations=2,
                    k_topics=2,
                    max_iter=1,
                    random_seed=42,
                    output_path=output_path
                )

            # Verify structure
            self.assertIn("n_permutations", result)
            self.assertEqual(result["n_permutations"], 2)
            self.assertIn("null_distributions", result)
            self.assertIn("2000-2004_2005-2009", result["null_distributions"])
            self.assertEqual(len(result["null_distributions"]["2000-2004_2005-2009"]), 2)
            self.assertIn("execution_time_seconds", result)
            self.assertIn("random_seed", result)

    def test_stratified_sample_empty_window(self):
        """Test handling of a window with no data."""
        data = [{"window": "w1", "tokens": ["a"]}]
        sampled = stratified_sample_by_window(data, ["w1", "w2"], max_per_window=2000, random_seed=42)
        self.assertEqual(len(sampled), 1)
        self.assertEqual(sampled[0]["window"], "w1")

if __name__ == "__main__":
    unittest.main()