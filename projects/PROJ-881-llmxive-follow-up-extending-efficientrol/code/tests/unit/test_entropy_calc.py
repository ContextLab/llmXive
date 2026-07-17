import pytest
import numpy as np
import sys
import os
from src.utils.entropy_calc import (
    compute_shannon_entropy,
    compute_batch_entropy,
    compute_layer_wise_entropy,
)

class TestComputeShannonEntropy:
    def test_basic_entropy(self):
        probs = [0.5, 0.5]
        entropy = compute_shannon_entropy(probs)
        assert abs(entropy - 1.0) < 1e-6

    def test_zero_probability_clamp(self):
        probs = [1.0, 0.0]
        entropy = compute_shannon_entropy(probs)
        assert entropy == 0.0

    def test_empty_input(self):
        with pytest.raises(ValueError):
            compute_shannon_entropy([])

class TestComputeBatchEntropy:
    def test_batch(self):
        probs_batch = [[0.5, 0.5], [0.8, 0.2]]
        entropies = compute_batch_entropy(probs_batch)
        assert len(entropies) == 2

class TestComputeLayerWiseEntropy:
    def test_layer_wise(self):
        # Mock layer outputs
        layer_probs = [[[0.5, 0.5], [0.5, 0.5]]] # 1 layer, 2 tokens
        entropies = compute_layer_wise_entropy(layer_probs)
        assert len(entropies) == 1
