import pytest
import numpy as np
import sys
import os
import torch
from src.utils.entropy_calc import (
    calculate_entropy,
    compute_shannon_entropy,
    compute_batch_entropy,
    compute_layer_wise_entropy
)


class TestCalculateEntropy:
    def test_basic_1d_uniform(self):
        """Test 1D uniform distribution: H = log(n)"""
        n = 4
        probs = torch.ones(n) / n
        entropy = calculate_entropy(probs)
        expected = np.log(n)
        assert abs(entropy - expected) < 1e-6

    def test_basic_2d_batch(self):
        """Test 2D batch processing returns mean"""
        batch_probs = torch.tensor([
            [0.5, 0.5, 0.0, 0.0],
            [0.0, 0.0, 0.5, 0.5]
        ])
        entropy = calculate_entropy(batch_probs)
        # Both rows have same entropy: -2 * 0.5 * log(0.5) = -log(0.5) = log(2)
        expected = np.log(2)
        assert abs(entropy - expected) < 1e-6

    def test_clamp_prevents_log_zero(self):
        """
        Semantic Test: The function MUST correctly handle near-zero probability inputs
        by returning a finite value without crashing.
        This test specifically asserts the function returns a finite value for input
        probabilities resulting in p=0.0 (which would be clamped to 1e-9).
        """
        # Create a distribution with exact zeros
        probs = torch.tensor([1.0, 0.0, 0.0, 0.0])
        
        # This should NOT raise an error and should return a finite value
        entropy = calculate_entropy(probs)
        
        # Verify the result is finite (not nan or inf)
        assert np.isfinite(entropy), f"Entropy should be finite, got {entropy}"
        
        # Verify it's non-negative (entropy is always >= 0)
        assert entropy >= 0.0, f"Entropy should be non-negative, got {entropy}"

    def test_clamp_extreme_values(self):
        """Test with extremely small probabilities"""
        probs = torch.tensor([1.0 - 1e-15, 1e-15, 0.0, 0.0])
        entropy = calculate_entropy(probs)
        assert np.isfinite(entropy)

    def test_gpu_tensor_raises_error(self):
        """Test that GPU tensors raise ValueError"""
        if torch.cuda.is_available():
            probs_gpu = torch.tensor([0.5, 0.5]).cuda()
            with pytest.raises(ValueError, match="must be on CPU"):
                calculate_entropy(probs_gpu)
        else:
            pytest.skip("CUDA not available")

    def test_empty_tensor_raises_error(self):
        """Test that empty tensors raise ValueError"""
        empty_probs = torch.tensor([])
        with pytest.raises(ValueError, match="empty"):
            calculate_entropy(empty_probs)

    def test_invalid_type_raises_error(self):
        """Test that invalid input types raise ValueError"""
        with pytest.raises(ValueError, match="must be torch.Tensor or numpy.ndarray"):
            calculate_entropy([0.5, 0.5])

    def test_wrong_dimensions_raises_error(self):
        """Test that 3D tensors raise ValueError"""
        wrong_shape = torch.randn(2, 3, 4)
        with pytest.raises(ValueError, match="must be 1D or 2D"):
            calculate_entropy(wrong_shape)

    def test_numpy_array_input(self):
        """Test that numpy arrays are accepted"""
        probs_np = np.array([0.5, 0.5])
        entropy = calculate_entropy(probs_np)
        assert np.isfinite(entropy)

    def test_deterministic_output(self):
        """Test that same input gives same output"""
        probs = torch.tensor([0.3, 0.7])
        e1 = calculate_entropy(probs)
        e2 = calculate_entropy(probs)
        assert e1 == e2


class TestComputeShannonEntropy:
    def test_alias_to_calculate_entropy(self):
        """Test that compute_shannon_entropy is an alias"""
        probs = torch.tensor([0.25, 0.75])
        e1 = calculate_entropy(probs)
        e2 = compute_shannon_entropy(probs)
        assert e1 == e2


class TestComputeBatchEntropy:
    def test_basic_batch(self):
        """Test batch entropy calculation"""
        batch_probs = torch.tensor([
            [0.5, 0.5],
            [1.0, 0.0]
        ])
        entropies = compute_batch_entropy(batch_probs)
        
        assert len(entropies) == 2
        assert np.isfinite(entropies[0])
        assert np.isfinite(entropies[1])
        
        # First item: uniform, entropy = log(2)
        expected_0 = np.log(2)
        assert abs(entropies[0] - expected_0) < 1e-6
        
        # Second item: deterministic, entropy = 0
        assert abs(entropies[1] - 0.0) < 1e-6

    def test_clamping_in_batch(self):
        """Test that zeros are clamped in batch processing"""
        batch_probs = torch.tensor([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]
        ])
        entropies = compute_batch_entropy(batch_probs)
        
        for e in entropies:
            assert np.isfinite(e)


class TestComputeLayerWiseEntropy:
    def test_basic_layer_wise(self):
        """Test layer-wise entropy calculation"""
        batch, layers, vocab = 2, 3, 4
        logits = torch.randn(batch, layers, vocab)
        
        results = compute_layer_wise_entropy(logits)
        
        assert len(results) == layers
        for layer_idx, entropies in results.items():
            assert len(entropies) == batch
            for e in entropies:
                assert np.isfinite(e)

    def test_specific_layer_indices(self):
        """Test with specific layer indices"""
        logits = torch.randn(2, 5, 4)
        results = compute_layer_wise_entropy(logits, layer_indices=[0, 2, 4])
        
        assert len(results) == 3
        assert 0 in results
        assert 2 in results
        assert 4 in results

    def test_invalid_layer_index(self):
        """Test that invalid layer index raises error"""
        logits = torch.randn(2, 3, 4)
        with pytest.raises(ValueError, match="out of range"):
            compute_layer_wise_entropy(logits, layer_indices=[5])

    def test_gpu_logits_raises_error(self):
        """Test that GPU logits raise ValueError"""
        if torch.cuda.is_available():
            logits_gpu = torch.randn(2, 3, 4).cuda()
            with pytest.raises(ValueError, match="must be on CPU"):
                compute_layer_wise_entropy(logits_gpu)
        else:
            pytest.skip("CUDA not available")

    def test_wrong_logits_dimensions(self):
        """Test that wrong dimensions raise error"""
        wrong_logits = torch.randn(2, 3)  # 2D instead of 3D
        with pytest.raises(ValueError, match="must be 3D"):
            compute_layer_wise_entropy(wrong_logits)