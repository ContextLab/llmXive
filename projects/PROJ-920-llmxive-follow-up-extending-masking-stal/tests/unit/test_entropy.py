"""
Unit tests for entropy.py utility functions.
Verifies Shannon entropy calculation and clamping for zero density (Edge Case, FR-008).
"""

import math
import sys
import os
import unittest
from pathlib import Path

# Add the project root to the path to allow imports from code/utils
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.entropy import calculate_shannon_entropy


class TestShannonEntropy(unittest.TestCase):
    """Tests for the calculate_shannon_entropy function."""

    def test_empty_string_returns_zero(self):
        """Test that an empty string returns an entropy of 0."""
        result = calculate_shannon_entropy("")
        self.assertEqual(result, 0.0)

    def test_single_byte_returns_zero(self):
        """Test that a single byte string returns an entropy of 0."""
        result = calculate_shannon_entropy("a")
        self.assertEqual(result, 0.0)

    def test_uniform_bytes_returns_zero(self):
        """Test that a string with only one unique byte returns entropy 0."""
        result = calculate_shannon_entropy("aaaaaa")
        self.assertEqual(result, 0.0)

    def test_two_equal_bytes_returns_one_bit(self):
        """Test entropy for two equiprobable symbols (should be 1.0 bit)."""
        # 'a' and 'b' each appear 50% of the time
        text = "ab"
        # Entropy = - (0.5 * log2(0.5) + 0.5 * log2(0.5)) = 1.0
        result = calculate_shannon_entropy(text)
        self.assertAlmostEqual(result, 1.0, places=5)

    def test_known_distribution(self):
        """Test entropy with a known distribution: 50% 'a', 25% 'b', 25% 'c'."""
        # Text: 4 'a's, 2 'b's, 2 'c's -> Total 8 chars
        text = "aaaabbcc"
        # p(a)=0.5, p(b)=0.25, p(c)=0.25
        # H = - (0.5*log2(0.5) + 0.25*log2(0.25) + 0.25*log2(0.25))
        # H = - (0.5*-1 + 0.25*-2 + 0.25*-2) = 0.5 + 0.5 + 0.5 = 1.5
        expected = 1.5
        result = calculate_shannon_entropy(text)
        self.assertAlmostEqual(result, expected, places=5)

    def test_utf8_multibyte_characters(self):
        """Test that UTF-8 multibyte characters are handled correctly as byte sequences."""
        # The character '€' (Euro sign) is 3 bytes in UTF-8: 0xE2 0x82 0xAC
        # If we repeat it, we get a uniform sequence of bytes -> entropy 0
        text = "€€€€"
        result = calculate_shannon_entropy(text)
        self.assertEqual(result, 0.0)

        # Mix of ASCII and UTF-8 to ensure byte-level processing
        # 'A' is 0x41, '€' is 0xE2, 0x82, 0xAC
        # Sequence: 0x41, 0xE2, 0x82, 0xAC, 0x41, 0xE2, 0x82, 0xAC
        # Unique bytes: 0x41, 0xE2, 0x82, 0xAC (4 unique)
        # Each appears 2 times out of 8 total -> p=0.25 for each
        # H = -4 * (0.25 * log2(0.25)) = -4 * (0.25 * -2) = 2.0
        text_mixed = "A€A€"
        result_mixed = calculate_shannon_entropy(text_mixed)
        self.assertAlmostEqual(result_mixed, 2.0, places=5)

    def test_clamping_for_zero_density(self):
        """
        Test the edge case where entropy might be 0 (zero density).
        The function should return 0.0 and not raise a division by zero or log(0) error.
        This verifies the 'clamping for zero density' requirement (Edge Case, FR-008).
        """
        # Cases that result in 0 entropy
        cases = [
            "",
            "a",
            "bbbbbb",
            "\x00\x00\x00",
            "€€€€€€"
        ]
        for case in cases:
            with self.subTest(text=case):
                result = calculate_shannon_entropy(case)
                self.assertEqual(result, 0.0)
                self.assertIsInstance(result, float)


if __name__ == "__main__":
    unittest.main()