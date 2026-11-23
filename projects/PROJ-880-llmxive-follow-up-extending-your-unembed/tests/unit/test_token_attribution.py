"""
Unit tests for token_attribution.py focusing on the 'mean embedding' projection logic.

This test suite verifies that compute_frequency_weighted_mean_embedding correctly
uses the EXTERNAL frequency distribution provided as input, and does NOT rely on
or fall back to any internal model token probabilities.

Requirement: T063 - Token Attribution Logic Verification
"""
import numpy as np
import pytest
from pathlib import Path
import json
import tempfile
import os

# Import the function under test
from token_attribution import compute_frequency_weighted_mean_embedding


class TestMeanEmbeddingProjection:
    """Tests for the mean embedding projection logic."""

    def test_uses_external_frequency_distribution(self):
        """
        Verify that the projection result is derived from the external frequency
        distribution, not internal model probabilities.
        
        Setup:
        - Create a mock W_E matrix (embedding matrix)
        - Create a mock external frequency distribution with specific values
        - Create a mock internal distribution (simulating model probabilities)
        
        Execution:
        - Call compute_frequency_weighted_mean_embedding with the external distribution
        
        Verification:
        - The result must match the manual calculation using ONLY the external distribution
        - The result must NOT match a calculation using the internal distribution
        """
        # Setup
        vocab_size = 100
        embedding_dim = 64
        
        # Create a deterministic mock embedding matrix (W_E)
        np.random.seed(42)
        W_E = np.random.randn(vocab_size, embedding_dim).astype(np.float32)
        
        # Create an external frequency distribution (e.g., from RedPajama)
        # We use a specific pattern: token 0 has freq 0.5, token 1 has freq 0.3, others 0.0
        external_freq_dist = {
            "language": "en",
            "total_tokens": 1000000,
            "unique_tokens": 2,
            "distribution": {
                "0": 0.5,
                "1": 0.3
            }
        }
        
        # Create a different internal distribution (e.g., model's own probabilities)
        # This should NOT affect the result
        internal_freq_dist = {
            "language": "en",
            "total_tokens": 1000000,
            "unique_tokens": 10,
            "distribution": {
                "0": 0.1,  # Different from external
                "1": 0.1,  # Different from external
                "2": 0.1,
                "3": 0.1,
                "4": 0.1,
                "5": 0.1,
                "6": 0.1,
                "7": 0.1,
                "8": 0.1,
                "9": 0.1
            }
        }
        
        # Write external distribution to a temp file (as the function expects)
        with tempfile.TemporaryDirectory() as tmpdir:
            freq_file = os.path.join(tmpdir, "external_freq.json")
            with open(freq_file, "w") as f:
                json.dump(external_freq_dist, f)
            
            # Call the function with the external distribution
            result = compute_frequency_weighted_mean_embedding(
                freq_file_path=freq_file,
                W_E=W_E,
                vocab_size=vocab_size
            )
            
            # Manual calculation using ONLY the external distribution
            # Expected result = sum(freq[token_id] * W_E[token_id]) for all tokens
            expected_result = np.zeros(embedding_dim, dtype=np.float32)
            for token_id_str, freq in external_freq_dist["distribution"].items():
                token_id = int(token_id_str)
                if token_id < vocab_size:
                    expected_result += freq * W_E[token_id]
            
            # Verify the result matches the external-based calculation
            np.testing.assert_array_almost_equal(
                result, 
                expected_result, 
                decimal=5,
                err_msg="Result does not match calculation using external frequency distribution"
            )
            
            # Verify the result does NOT match the internal-based calculation
            internal_expected_result = np.zeros(embedding_dim, dtype=np.float32)
            for token_id_str, freq in internal_freq_dist["distribution"].items():
                token_id = int(token_id_str)
                if token_id < vocab_size:
                    internal_expected_result += freq * W_E[token_id]
            
            # If the function incorrectly used internal probabilities, these would be equal
            with pytest.raises(AssertionError):
                np.testing.assert_array_almost_equal(
                    result,
                    internal_expected_result,
                    decimal=5
                )

    def test_zero_external_frequency_yields_zero_projection(self):
        """
        Verify that if the external frequency distribution is all zeros,
        the result is a zero vector.
        """
        vocab_size = 50
        embedding_dim = 32
        
        np.random.seed(123)
        W_E = np.random.randn(vocab_size, embedding_dim).astype(np.float32)
        
        # All zero frequency distribution
        zero_freq_dist = {
            "language": "en",
            "total_tokens": 1000,
            "unique_tokens": 0,
            "distribution": {}
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            freq_file = os.path.join(tmpdir, "zero_freq.json")
            with open(freq_file, "w") as f:
                json.dump(zero_freq_dist, f)
            
            result = compute_frequency_weighted_mean_embedding(
                freq_file_path=freq_file,
                W_E=W_E,
                vocab_size=vocab_size
            )
            
            # Should be a zero vector
            expected = np.zeros(embedding_dim, dtype=np.float32)
            np.testing.assert_array_almost_equal(
                result,
                expected,
                decimal=5
            )

    def test_single_token_frequency(self):
        """
        Verify correct behavior when only one token has non-zero frequency.
        """
        vocab_size = 20
        embedding_dim = 16
        
        np.random.seed(456)
        W_E = np.random.randn(vocab_size, embedding_dim).astype(np.float32)
        
        # Only token 5 has frequency 1.0
        single_token_freq = {
            "language": "en",
            "total_tokens": 1000,
            "unique_tokens": 1,
            "distribution": {
                "5": 1.0
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            freq_file = os.path.join(tmpdir, "single_token.json")
            with open(freq_file, "w") as f:
                json.dump(single_token_freq, f)
            
            result = compute_frequency_weighted_mean_embedding(
                freq_file_path=freq_file,
                W_E=W_E,
                vocab_size=vocab_size
            )
            
            # Should equal exactly W_E[5]
            expected = W_E[5]
            np.testing.assert_array_almost_equal(
                result,
                expected,
                decimal=5
            )

    def test_normalization_factor(self):
        """
        Verify that the function correctly normalizes by total frequency.
        The mean embedding should be the weighted average, not just the sum.
        """
        vocab_size = 10
        embedding_dim = 8
        
        np.random.seed(789)
        W_E = np.random.randn(vocab_size, embedding_dim).astype(np.float32)
        
        # Two tokens with frequencies that sum to 2.0
        # Token 0: 0.6, Token 1: 1.4
        # Mean = (0.6 * W_E[0] + 1.4 * W_E[1]) / (0.6 + 1.4)
        freq_dist = {
            "language": "en",
            "total_tokens": 1000,
            "unique_tokens": 2,
            "distribution": {
                "0": 0.6,
                "1": 1.4
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            freq_file = os.path.join(tmpdir, "norm_test.json")
            with open(freq_file, "w") as f:
                json.dump(freq_dist, f)
            
            result = compute_frequency_weighted_mean_embedding(
                freq_file_path=freq_file,
                W_E=W_E,
                vocab_size=vocab_size
            )
            
            # Manual calculation with normalization
            total_freq = 0.6 + 1.4
            expected = (0.6 * W_E[0] + 1.4 * W_E[1]) / total_freq
            
            np.testing.assert_array_almost_equal(
                result,
                expected,
                decimal=5
            )