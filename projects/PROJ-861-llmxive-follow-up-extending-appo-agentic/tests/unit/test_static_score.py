"""
Unit tests for static scoring probability clamping logic.

Tests the epsilon smoothing factor (1e-9) to prevent NaN values
when computing log(0) in KL divergence calculations.
"""
import pytest
import numpy as np
from typing import List


# Constants matching the implementation requirements
EPSILON = 1e-9
FLOOR_PROBABILITY = EPSILON


def clamp_probabilities(probs: List[float], floor: float = FLOOR_PROBABILITY) -> List[float]:
    """
    Clamp probabilities to prevent log(0).
    
    Args:
        probs: List of raw probability values.
        floor: Minimum probability floor (default 1e-9).
        
    Returns:
        List of clamped probabilities.
    """
    return [max(p, floor) for p in probs]


def compute_log_probs(probs: List[float]) -> List[float]:
    """
    Compute log probabilities safely after clamping.
    
    Args:
        probs: List of clamped probability values.
        
    Returns:
        List of log probability values.
    """
    return [np.log(p) for p in probs]


def compute_kl_divergence(p: List[float], q: List[float]) -> float:
    """
    Compute KL divergence D_KL(P || Q) with probability clamping.
    
    Args:
        p: Distribution P (raw probabilities).
        q: Distribution Q (raw probabilities).
        
    Returns:
        KL divergence value.
    """
    p_clamped = clamp_probabilities(p)
    q_clamped = clamp_probabilities(q)
    
    log_p = compute_log_probs(p_clamped)
    log_q = compute_log_probs(q_clamped)
    
    # D_KL(P || Q) = sum(P(x) * log(P(x) / Q(x)))
    kl = 0.0
    for p_val, log_p_val, log_q_val in zip(p_clamped, log_p, log_q):
        kl += p_val * (log_p_val - log_q_val)
        
    return kl


class TestProbabilityClamping:
    """Tests for probability clamping to prevent NaN in log calculations."""

    def test_clamp_below_floor(self):
        """Test that probabilities below floor are clamped to floor."""
        raw_probs = [0.0, 1e-15, 1e-10, 0.5, 1.0]
        clamped = clamp_probabilities(raw_probs, floor=EPSILON)
        
        expected = [EPSILON, EPSILON, EPSILON, 0.5, 1.0]
        
        for c, e in zip(clamped, expected):
            assert abs(c - e) < 1e-12, f"Expected {e}, got {c}"

    def test_clamp_preserves_above_floor(self):
        """Test that probabilities above floor remain unchanged."""
        raw_probs = [1e-8, 0.01, 0.5, 0.999]
        clamped = clamp_probabilities(raw_probs, floor=EPSILON)
        
        for r, c in zip(raw_probs, clamped):
            assert r == c, f"Value {r} was changed to {c}"

    def test_log_no_nan_after_clamp(self):
        """Test that log calculation produces no NaN after clamping."""
        raw_probs = [0.0, 1e-20, 0.5]
        clamped = clamp_probabilities(raw_probs)
        log_probs = compute_log_probs(clamped)
        
        for lp in log_probs:
            assert not np.isnan(lp), f"Log probability {lp} is NaN"
            assert not np.isinf(lp), f"Log probability {lp} is Inf"

    def test_kl_divergence_no_nan_with_zero_probs(self):
        """Test that KL divergence handles zero probabilities without NaN."""
        p = [0.0, 0.5, 0.5]
        q = [0.0, 0.0, 1.0]
        
        kl = compute_kl_divergence(p, q)
        
        assert not np.isnan(kl), f"KL divergence {kl} is NaN"
        assert not np.isinf(kl), f"KL divergence {kl} is Inf"
        assert kl >= 0.0, f"KL divergence {kl} should be non-negative"

    def test_epsilon_value_is_correct(self):
        """Verify the epsilon floor is exactly 1e-9."""
        assert FLOOR_PROBABILITY == 1e-9, f"Floor should be 1e-9, got {FLOOR_PROBABILITY}"

    def test_clamp_with_custom_floor(self):
        """Test clamping with a custom floor value."""
        custom_floor = 1e-5
        raw_probs = [0.0, 1e-6, 1e-4, 0.5]
        clamped = clamp_probabilities(raw_probs, floor=custom_floor)
        
        expected = [custom_floor, custom_floor, 1e-4, 0.5]
        
        for c, e in zip(clamped, expected):
            assert abs(c - e) < 1e-12, f"Expected {e}, got {c}"

    def test_all_zero_input(self):
        """Test behavior when all input probabilities are zero."""
        raw_probs = [0.0, 0.0, 0.0]
        clamped = clamp_probabilities(raw_probs)
        
        for c in clamped:
            assert c == EPSILON, f"Expected {EPSILON}, got {c}"

        # Should still produce valid log probs
        log_probs = compute_log_probs(clamped)
        for lp in log_probs:
            assert not np.isnan(lp), "Log probability is NaN"

    def test_clamp_preserves_sum_approximation(self):
        """Test that clamping doesn't drastically alter distribution shape."""
        raw_probs = [0.1, 0.2, 0.3, 0.4]
        clamped = clamp_probabilities(raw_probs)
        
        # Original sum
        orig_sum = sum(raw_probs)
        # Clamped sum (should be very close)
        clamp_sum = sum(clamped)
        
        assert abs(orig_sum - clamp_sum) < 1e-10, "Clamping altered distribution sum significantly"

    def test_edge_case_very_small_positive(self):
        """Test handling of very small positive probabilities."""
        raw_probs = [1e-100, 1e-50, 1e-10]
        clamped = clamp_probabilities(raw_probs)
        
        # Values below 1e-9 should be clamped
        assert clamped[0] == EPSILON
        assert clamped[1] == EPSILON
        # Values above 1e-9 should remain
        assert clamped[2] == 1e-10

    def test_kl_divergence_symmetry_check(self):
        """Basic check that KL divergence is computed (not necessarily symmetric)."""
        p = [0.2, 0.8]
        q = [0.8, 0.2]
        
        kl_pq = compute_kl_divergence(p, q)
        kl_qp = compute_kl_divergence(q, p)
        
        # Both should be finite and non-negative
        assert not np.isnan(kl_pq)
        assert not np.isnan(kl_qp)
        assert kl_pq >= 0.0
        assert kl_qp >= 0.0
        # They should generally differ (KL is not symmetric)
        assert abs(kl_pq - kl_qp) > 1e-6, "KL divergence should not be symmetric"