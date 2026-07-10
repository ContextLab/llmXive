import unittest
import numpy as np
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'code'))

from data.extract_features import calculate_shannon_entropy, one_hot_encode, filter_sequence_by_entropy

class TestExtractFeatures(unittest.TestCase):

    def test_shannon_entropy_max(self):
        # Random sequence should have high entropy
        seq = "ACGTACGTACGTACGT"
        entropy = calculate_shannon_entropy(seq)
        self.assertGreater(entropy, 1.5) # Should be close to 2.0 for random

    def test_shannon_entropy_low(self):
        # Homopolymer should have low entropy
        seq = "AAAAAAAAAAAAAAA"
        entropy = calculate_shannon_entropy(seq)
        self.assertEqual(entropy, 0.0)

    def test_one_hot_encode(self):
        seq = "ACGT"
        encoded = one_hot_encode(seq)
        self.assertEqual(encoded.shape, (4, 4))
        # Check A
        self.assertListEqual(encoded[0].tolist(), [1, 0, 0, 0])
        # Check C
        self.assertListEqual(encoded[1].tolist(), [0, 1, 0, 0])

    def test_filter_sequence_by_entropy(self):
        seq_high = "ACGTACGTACGT"
        seq_low = "AAAAAAAAAAAA"
        
        self.assertTrue(filter_sequence_by_entropy(seq_high, threshold=0.8))
        self.assertFalse(filter_sequence_by_entropy(seq_low, threshold=0.8))

    def test_one_hot_encode_n(self):
        seq = "N"
        encoded = one_hot_encode(seq)
        # N should be uniform
        self.assertListEqual(encoded[0].tolist(), [0.25, 0.25, 0.25, 0.25])

if __name__ == '__main__':
    unittest.main()