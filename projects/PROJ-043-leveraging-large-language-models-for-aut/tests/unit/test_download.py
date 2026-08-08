import unittest
from code.utils.cache import compute_hash
import datasets
import pandas as pd

class TestDatasetSampling(unittest.TestCase):
    def test_sampling_logic(self):
        # Mock the dataset loading to avoid actual download during testing
        mock_dataset = datasets.Dataset.from_dict({
            'code': ['function1', 'function2', 'function3', 'function4', 'function5'],
            'hash': ['hash1', 'hash2', 'hash3', 'hash4', 'hash5']
        })

        def mock_load_dataset(*args, **kwargs):
            return mock_dataset

        datasets.load_dataset = mock_load_dataset

        from code.data.download import sample_dataset  # Import here to avoid circular dependency

        sampled_dataset = sample_dataset(max_samples=3)

        self.assertEqual(len(sampled_dataset), 3)
        # Check that the sampled dataset contains unique hashes
        hashes = set(sampled_dataset['hash'])
        self.assertEqual(len(hashes), len(sampled_dataset))

        # Test compute_hash function for consistency
        test_code1 = "def test_function(): pass"
        test_code2 = "def test_function(): pass"  # Same code
        test_hash1 = compute_hash(test_code1)
        test_hash2 = compute_hash(test_code2)

        self.assertEqual(test_hash1, test_hash2)
