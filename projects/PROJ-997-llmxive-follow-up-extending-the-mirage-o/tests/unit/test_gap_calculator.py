"""
T010: Unit test for KL divergence calculation edge cases.
Tests zero-divergence and numerical stability.
"""
import pytest
import torch
import numpy as np

from src.services.gap_calculator import compute_kl_divergence, calculate_gap

def test_compute_kl_divergence_identical_logits():
    """Test KL divergence with identical logits (should be ~0)."""
    logits = torch.randn(1, 10, 128)
    kl = compute_kl_divergence(logits, logits)
    assert kl < 1e-5, f"Expected near-zero KL for identical logits, got {kl}"

def test_compute_kl_divergence_different_logits():
    """Test KL divergence with different logits (should be > 0)."""
    logits1 = torch.randn(1, 10, 128)
    logits2 = torch.randn(1, 10, 128) * 2  # Different distribution
    kl = compute_kl_divergence(logits1, logits2)
    assert kl > 0, f"Expected positive KL for different logits, got {kl}"

def test_compute_kl_divergence_epsilon_stability():
    """Test numerical stability with epsilon."""
    # Create logits that might cause numerical issues
    logits1 = torch.zeros(1, 10, 128)
    logits2 = torch.zeros(1, 10, 128)
    kl = compute_kl_divergence(logits1, logits2, epsilon=1e-8)
    assert not np.isnan(kl), "KL divergence should not be NaN with epsilon"
    assert not np.isinf(kl), "KL divergence should not be Inf with epsilon"

def test_calculate_gap_with_missing_logits():
    """Test gap calculation with missing logits."""
    fp_result = {"logits": torch.randn(1, 10, 128)}
    q_result = {}  # Missing logits
    
    gap = calculate_gap(fp_result, q_result)
    assert gap is None, "Should return None when logits are missing"

def test_calculate_gap_with_numpy_arrays():
    """Test gap calculation with numpy arrays."""
    fp_logits = np.random.randn(1, 10, 128).astype(np.float32)
    q_logits = np.random.randn(1, 10, 128).astype(np.float32)
    
    fp_result = {"logits": fp_logits}
    q_result = {"logits": q_logits}
    
    gap = calculate_gap(fp_result, q_result)
    assert gap is not None, "Should handle numpy arrays"
    assert isinstance(gap, float), "Should return float"