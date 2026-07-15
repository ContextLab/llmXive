"""
Integration test for FID comparison in the llmXive pipeline.

This test verifies that the FID calculation logic in `src.metrics`
works correctly on a set of dummy (synthetic) samples to ensure the
integration path (loading images -> extracting features -> computing FID)
is valid.

NOTE: This test uses synthetic random tensors to simulate image features
for the purpose of verifying the calculation pipeline. It does NOT
evaluate model quality, only the correctness of the FID computation
machinery.
"""
import pytest
import torch
import numpy as np
from pathlib import Path
import sys
import os

# Ensure the src directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.metrics import calculate_fid


class TestFIDComparison:
    """Integration tests for FID calculation."""

    def test_fid_computation_on_dummy_samples(self):
        """
        Verify FID calculation on dummy samples.

        Generates two sets of random tensors representing features
        (simulating Inception-v3 pool3 outputs) and ensures the
        calculate_fid function returns a valid float without error.
        """
        # Setup: Generate dummy feature sets
        # Shape: (N, D) where N is number of samples, D is feature dimension (2048 for Inception)
        num_samples = 100
        feature_dim = 2048
        seed_a = 42
        seed_b = 123

        torch.manual_seed(seed_a)
        features_1 = torch.randn(num_samples, feature_dim)

        torch.manual_seed(seed_b)
        features_2 = torch.randn(num_samples, feature_dim)

        # Execute: Calculate FID
        # The function expects lists of tensors or numpy arrays
        fid_score = calculate_fid(features_1, features_2)

        # Verify: Result is a float and non-negative
        assert isinstance(fid_score, float), "FID score must be a float"
        assert fid_score >= 0.0, "FID score must be non-negative"
        assert not np.isnan(fid_score), "FID score must not be NaN"
        assert not np.isinf(fid_score), "FID score must not be Inf"

        # Verify: Different distributions yield higher FID than identical ones
        # (Sanity check: identical distributions should have FID ~ 0)
        torch.manual_seed(seed_a)
        features_identical = torch.randn(num_samples, feature_dim)

        fid_same = calculate_fid(features_identical, features_identical)
        
        # Due to floating point noise, identical samples won't be exactly 0, but should be very low
        assert fid_same < 0.1, f"FID for identical distributions should be near zero, got {fid_same}"
        
        # Different distributions should be significantly higher
        assert fid_score > fid_same, "FID for different distributions should be higher than identical"

    def test_fid_with_different_sample_sizes(self):
        """
        Verify FID calculation handles different sample sizes.
        """
        num_samples_1 = 50
        num_samples_2 = 150
        feature_dim = 2048

        torch.manual_seed(100)
        features_1 = torch.randn(num_samples_1, feature_dim)

        torch.manual_seed(200)
        features_2 = torch.randn(num_samples_2, feature_dim)

        fid_score = calculate_fid(features_1, features_2)

        assert isinstance(fid_score, float)
        assert fid_score >= 0.0

    def test_fid_with_numpy_inputs(self):
        """
        Verify FID calculation accepts numpy arrays as input.
        """
        num_samples = 100
        feature_dim = 2048

        np.random.seed(55)
        features_1 = np.random.randn(num_samples, feature_dim).astype(np.float32)

        np.random.seed(66)
        features_2 = np.random.randn(num_samples, feature_dim).astype(np.float32)

        fid_score = calculate_fid(features_1, features_2)

        assert isinstance(fid_score, float)
        assert fid_score >= 0.0