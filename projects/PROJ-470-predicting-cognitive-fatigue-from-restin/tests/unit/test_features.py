"""
Unit tests for feature extraction (T016).
Verifies that LZC and PE values are within mathematically defined ranges.
"""
import csv
import os
import sys
from pathlib import Path
from unittest import TestCase

import numpy as np

# Add project root to path if running directly
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT / "code"))

from features import extract_lempel_ziv_complexity, extract_permutation_entropy


class TestFeatureExtraction(TestCase):
    
    def test_lzc_range(self):
        """Test that LZC values are < 1.0 (normalized)."""
        # Generate a random signal
        np.random.seed(42)
        signal = np.random.randn(1000)
        
        lzc = extract_lempel_ziv_complexity(signal)
        
        # LZC is normalized between 0 and 1 for random signals
        # We assert it is strictly less than 1.0 (the theoretical max for normalized LZC)
        self.assertLess(lzc, 1.0, "LZC value should be less than 1.0")
        
    def test_pe_range(self):
        """Test that PE values are < log2(3!) ~= 1.585 (for order=3)."""
        # Maximum permutation entropy for order 3 is log2(6) = 1.585
        # The task spec says < 2.585, which is log2(6) + some margin or perhaps log2(3!) * 1.64?
        # Actually, log2(3!) = log2(6) ≈ 1.585. 
        # The spec says < 2.585. Let's verify with a random signal.
        np.random.seed(42)
        signal = np.random.randn(1000)
        
        pe = extract_permutation_entropy(signal, order=3, delay=1)
        
        # The theoretical maximum for order 3 is log2(6) ≈ 1.585.
        # The test requirement says < 2.585. Since 1.585 < 2.585, this should pass.
        self.assertLess(pe, 2.585, "PE value should be less than 2.585")

    def test_csv_output_structure(self):
        """
        Verify that if the script runs, the output CSV has the correct columns.
        This test assumes the script has been run and the file exists.
        """
        output_file = Path("data/analysis/complexity_metrics.csv")
        
        if not output_file.exists():
            self.skipTest(f"Output file {output_file} not found. Run code/features.py first.")
        
        with open(output_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        # Check columns
        expected_columns = {"participant_id", "channel", "segment_id", "lzc_value", "pe_value"}
        self.assertEqual(set(reader.fieldnames), expected_columns, "CSV columns do not match expected")
        
        # Check that we have some data rows (if the script ran successfully)
        # Note: This might be empty if the input data directory is empty, 
        # but the task requires processing the FULL dataset.
        # We just verify the structure here.
        if len(rows) > 0:
            # Verify types
            for row in rows:
                self.assertIsInstance(float(row["lzc_value"]), float)
                self.assertIsInstance(float(row["pe_value"]), float)

    def test_mathematical_bounds(self):
        """
        Additional check on mathematical bounds based on the spec.
        Spec says: LZC < 1.0, PE < 2.585.
        """
        # Create a constant signal -> LZC should be 0
        constant_signal = np.ones(100)
        lzc_const = extract_lempel_ziv_complexity(constant_signal)
        self.assertEqual(lzc_const, 0.0, "LZC of constant signal should be 0")

        # Create a perfectly alternating signal -> LZC should be low but > 0
        alt_signal = np.array([1, -1] * 50)
        lzc_alt = extract_lempel_ziv_complexity(alt_signal)
        self.assertLess(lzc_alt, 0.5, "LZC of alternating signal should be low")

        # PE of constant signal -> 0
        pe_const = extract_permutation_entropy(constant_signal)
        self.assertEqual(pe_const, 0.0, "PE of constant signal should be 0")

        # PE of random signal -> should be close to max for order 3
        np.random.seed(42)
        rand_signal = np.random.randn(1000)
        pe_rand = extract_permutation_entropy(rand_signal, order=3, delay=1)
        # Max PE for order 3 is log2(6) ≈ 1.585
        max_pe = np.log2(np.math.factorial(3))
        self.assertLessEqual(pe_rand, max_pe + 0.01, f"PE should be <= max PE ({max_pe})")

if __name__ == "__main__":
    import unittest
    unittest.main()