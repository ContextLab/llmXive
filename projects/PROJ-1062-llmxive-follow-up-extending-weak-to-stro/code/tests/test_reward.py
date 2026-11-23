"""
Unit tests for reward calculation logic and epsilon-smoothing.

Tests verify:
1. Implicit reward calculation correctness
2. Epsilon-smoothing prevents division by zero and log(0)
3. Numerical stability with extreme probability values
4. Consistency with theoretical expectations
"""
import pytest
import numpy as np
import torch
from typing import Dict, Any, List, Tuple

# Import from the existing API surface
from core.reward_computation import (
    ImplicitRewardComputer,
    compute_implicit_reward,
    validate_reward_computation
)


class TestImplicitRewardComputer:
    """Tests for the ImplicitRewardComputer class."""
    
    def test_initialization_default_epsilon(self):
        """Test that default epsilon value is set correctly."""
        computer = ImplicitRewardComputer()
        assert computer.epsilon == 1e-8
        assert computer.device == "cpu"
    
    def test_initialization_custom_epsilon(self):
        """Test custom epsilon configuration."""
        custom_epsilon = 1e-6
        computer = ImplicitRewardComputer(epsilon=custom_epsilon)
        assert computer.epsilon == custom_epsilon
    
    def test_initialization_device(self):
        """Test device configuration."""
        computer = ImplicitRewardComputer(device="cpu")
        assert computer.device == "cpu"
    
    def test_compute_reward_basic_case(self):
        """Test basic reward computation with valid probabilities."""
        computer = ImplicitRewardComputer(epsilon=1e-8)
        
        # Student and teacher probabilities (both valid, non-zero)
        student_probs = torch.tensor([0.8, 0.1, 0.1])
        teacher_probs = torch.tensor([0.7, 0.2, 0.1])
        
        reward = computer.compute_reward(student_probs, teacher_probs)
        
        # Reward should be log(student/teacher) with smoothing
        expected = torch.log(student_probs / teacher_probs)
        assert torch.allclose(reward, expected, atol=1e-6)
    
    def test_compute_reward_epsilon_smoothing(self):
        """Test that epsilon smoothing prevents division by zero."""
        computer = ImplicitRewardComputer(epsilon=1e-8)
        
        # Teacher probability is extremely small (near zero)
        student_probs = torch.tensor([0.5, 0.3, 0.2])
        teacher_probs = torch.tensor([1e-10, 0.5, 0.5])
        
        # Should not raise an error due to epsilon smoothing
        reward = computer.compute_reward(student_probs, teacher_probs)
        
        # Verify reward is finite (no inf or nan)
        assert torch.isfinite(reward).all()
        
        # The first element should use smoothed value
        expected_first = torch.log(student_probs[0] / (teacher_probs[0] + computer.epsilon))
        assert torch.isclose(reward[0], expected_first, atol=1e-8)
    
    def test_compute_reward_zero_student_prob(self):
        """Test handling of zero student probability."""
        computer = ImplicitRewardComputer(epsilon=1e-8)
        
        student_probs = torch.tensor([0.0, 0.5, 0.5])
        teacher_probs = torch.tensor([0.3, 0.35, 0.35])
        
        # Should not raise error, should produce very negative reward
        reward = computer.compute_reward(student_probs, teacher_probs)
        
        # First element should be very negative but finite
        assert torch.isfinite(reward[0])
        assert reward[0] < -10  # log(epsilon) is large negative
    
    def test_compute_reward_batched(self):
        """Test batched reward computation."""
        computer = ImplicitRewardComputer()
        
        batch_size = 4
        vocab_size = 100
        
        student_probs = torch.rand(batch_size, vocab_size)
        teacher_probs = torch.rand(batch_size, vocab_size)
        
        # Normalize to sum to 1
        student_probs = student_probs / student_probs.sum(dim=-1, keepdim=True)
        teacher_probs = teacher_probs / teacher_probs.sum(dim=-1, keepdim=True)
        
        reward = computer.compute_reward(student_probs, teacher_probs)
        
        assert reward.shape == (batch_size, vocab_size)
        assert torch.isfinite(reward).all()
    
    def test_compute_reward_2d_tokens(self):
        """Test token-level reward computation."""
        computer = ImplicitRewardComputer()
        
        seq_len = 20
        vocab_size = 1000
        
        student_probs = torch.rand(seq_len, vocab_size)
        teacher_probs = torch.rand(seq_len, vocab_size)
        
        student_probs = student_probs / student_probs.sum(dim=-1, keepdim=True)
        teacher_probs = teacher_probs / teacher_probs.sum(dim=-1, keepdim=True)
        
        reward = computer.compute_reward(student_probs, teacher_probs)
        
        assert reward.shape == (seq_len, vocab_size)
        assert torch.isfinite(reward).all()
    
    def test_compute_reward_consistency(self):
        """Test that repeated computations are deterministic."""
        computer = ImplicitRewardComputer()
        
        student_probs = torch.tensor([0.6, 0.3, 0.1])
        teacher_probs = torch.tensor([0.5, 0.35, 0.15])
        
        reward1 = computer.compute_reward(student_probs, teacher_probs)
        reward2 = computer.compute_reward(student_probs, teacher_probs)
        
        assert torch.allclose(reward1, reward2)


class TestComputeImplicitReward:
    """Tests for the standalone compute_implicit_reward function."""
    
    def test_function_basic(self):
        """Test basic functionality of compute_implicit_reward."""
        student_probs = torch.tensor([0.7, 0.2, 0.1])
        teacher_probs = torch.tensor([0.6, 0.3, 0.1])
        epsilon = 1e-8
        
        reward = compute_implicit_reward(student_probs, teacher_probs, epsilon)
        
        assert reward.shape == student_probs.shape
        assert torch.isfinite(reward).all()
    
    def test_function_epsilon_smoothing(self):
        """Test epsilon smoothing in standalone function."""
        student_probs = torch.tensor([0.5, 0.5])
        teacher_probs = torch.tensor([1e-15, 0.5])
        epsilon = 1e-8
        
        reward = compute_implicit_reward(student_probs, teacher_probs, epsilon)
        
        # Should be finite due to smoothing
        assert torch.isfinite(reward).all()
    
    def test_function_different_dtypes(self):
        """Test with different floating point types."""
        student_probs_f32 = torch.tensor([0.5, 0.5], dtype=torch.float32)
        teacher_probs_f32 = torch.tensor([0.3, 0.7], dtype=torch.float32)
        
        reward_f32 = compute_implicit_reward(student_probs_f32, teacher_probs_f32)
        
        student_probs_f64 = student_probs_f32.double()
        teacher_probs_f64 = teacher_probs_f32.double()
        
        reward_f64 = compute_implicit_reward(student_probs_f64, teacher_probs_f64)
        
        assert reward_f32.dtype == torch.float32
        assert reward_f64.dtype == torch.float64
        assert torch.allclose(reward_f32.float(), reward_f64.float(), atol=1e-5)
    
    def test_function_2d_input(self):
        """Test with 2D input (batch or sequence)."""
        student_probs = torch.rand(5, 100)
        teacher_probs = torch.rand(5, 100)
        
        student_probs = student_probs / student_probs.sum(dim=-1, keepdim=True)
        teacher_probs = teacher_probs / teacher_probs.sum(dim=-1, keepdim=True)
        
        reward = compute_implicit_reward(student_probs, teacher_probs)
        
        assert reward.shape == (5, 100)
        assert torch.isfinite(reward).all()


class TestValidateRewardComputation:
    """Tests for the validation function."""
    
    def test_validation_pass(self):
        """Test validation with valid inputs."""
        student_probs = torch.tensor([0.5, 0.3, 0.2])
        teacher_probs = torch.tensor([0.4, 0.4, 0.2])
        
        is_valid, message = validate_reward_computation(
            student_probs, teacher_probs, epsilon=1e-8
        )
        
        assert is_valid
        assert "valid" in message.lower() or len(message) > 0
    
    def test_validation_zero_sum(self):
        """Test validation catches zero-sum probabilities."""
        student_probs = torch.zeros(3)
        teacher_probs = torch.tensor([0.5, 0.3, 0.2])
        
        is_valid, message = validate_reward_computation(
            student_probs, teacher_probs, epsilon=1e-8
        )
        
        assert not is_valid
        assert "zero" in message.lower() or "sum" in message.lower()
    
    def test_validation_negative_probs(self):
        """Test validation catches negative probabilities."""
        student_probs = torch.tensor([0.5, -0.1, 0.6])
        teacher_probs = torch.tensor([0.4, 0.4, 0.2])
        
        is_valid, message = validate_reward_computation(
            student_probs, teacher_probs, epsilon=1e-8
        )
        
        assert not is_valid
        assert "negative" in message.lower() or "valid" in message.lower()
    
    def test_validation_shape_mismatch(self):
        """Test validation catches shape mismatches."""
        student_probs = torch.tensor([0.5, 0.3, 0.2])
        teacher_probs = torch.tensor([0.4, 0.4])
        
        is_valid, message = validate_reward_computation(
            student_probs, teacher_probs, epsilon=1e-8
        )
        
        assert not is_valid
        assert "shape" in message.lower() or "mismatch" in message.lower()
    
    def test_validation_extreme_values(self):
        """Test validation with extreme but valid values."""
        student_probs = torch.tensor([1.0 - 1e-10, 1e-10, 0.0])
        teacher_probs = torch.tensor([1e-10, 1.0 - 1e-10, 0.0])
        
        # Should pass validation due to epsilon smoothing
        is_valid, message = validate_reward_computation(
            student_probs, teacher_probs, epsilon=1e-8
        )
        
        # Validation should pass as long as shapes match and no negative values
        assert is_valid


class TestEpsilonSmoothingEdgeCases:
    """Specific tests for epsilon-smoothing edge cases."""
    
    def test_epsilon_prevents_log_zero(self):
        """Verify epsilon prevents log(0) when student prob is 0."""
        computer = ImplicitRewardComputer(epsilon=1e-8)
        
        student_probs = torch.tensor([0.0, 0.5, 0.5])
        teacher_probs = torch.tensor([0.3, 0.35, 0.35])
        
        reward = computer.compute_reward(student_probs, teacher_probs)
        
        # log(0) would be -inf, but with epsilon it should be finite
        assert torch.isfinite(reward[0])
        assert reward[0] == torch.log(computer.epsilon / teacher_probs[0])
    
    def test_epsilon_prevents_division_zero(self):
        """Verify epsilon prevents division by zero when teacher prob is 0."""
        computer = ImplicitRewardComputer(epsilon=1e-8)
        
        student_probs = torch.tensor([0.5, 0.3, 0.2])
        teacher_probs = torch.tensor([0.0, 0.5, 0.5])
        
        reward = computer.compute_reward(student_probs, teacher_probs)
        
        # Should be finite
        assert torch.isfinite(reward[0])
        assert reward[0] == torch.log(student_probs[0] / computer.epsilon)
    
    def test_epsilon_tuning_impact(self):
        """Test that different epsilon values produce different results near zero."""
        student_probs = torch.tensor([0.5, 0.3, 0.2])
        teacher_probs = torch.tensor([1e-15, 0.5, 0.5])
        
        reward_small_eps = compute_implicit_reward(student_probs, teacher_probs, epsilon=1e-10)
        reward_large_eps = compute_implicit_reward(student_probs, teacher_probs, epsilon=1e-5)
        
        # Results should differ at the problematic index
        assert not torch.allclose(reward_small_eps[0], reward_large_eps[0])
        
        # Both should be finite
        assert torch.isfinite(reward_small_eps[0])
        assert torch.isfinite(reward_large_eps[0])
    
    def test_epsilon_not_applied_when_not_needed(self):
        """Verify epsilon is not applied when probabilities are well-behaved."""
        computer = ImplicitRewardComputer(epsilon=1e-8)
        
        # Well-behaved probabilities (no zeros or near-zeros)
        student_probs = torch.tensor([0.4, 0.4, 0.2])
        teacher_probs = torch.tensor([0.3, 0.4, 0.3])
        
        reward = computer.compute_reward(student_probs, teacher_probs)
        expected = torch.log(student_probs / teacher_probs)
        
        # Should match exactly (within floating point precision)
        assert torch.allclose(reward, expected, atol=1e-7)


class TestNumericalStability:
    """Tests for numerical stability with extreme values."""
    
    def test_extreme_probability_ratio(self):
        """Test with very large probability ratios."""
        computer = ImplicitRewardComputer()
        
        student_probs = torch.tensor([0.999999, 0.000001, 0.0])
        teacher_probs = torch.tensor([0.000001, 0.999999, 0.0])
        
        reward = computer.compute_reward(student_probs, teacher_probs)
        
        # Should be finite despite extreme ratios
        assert torch.isfinite(reward).all()
    
    def test_very_small_probabilities(self):
        """Test with very small but non-zero probabilities."""
        computer = ImplicitRewardComputer()
        
        student_probs = torch.tensor([1e-15, 0.5, 0.5])
        teacher_probs = torch.tensor([0.5, 0.25, 0.25])
        
        reward = computer.compute_reward(student_probs, teacher_probs)
        
        assert torch.isfinite(reward).all()
    
    def test_large_batch_stability(self):
        """Test stability with large batches."""
        computer = ImplicitRewardComputer()
        
        batch_size = 1000
        vocab_size = 10000
        
        # Create probabilities with some extreme values
        student_probs = torch.rand(batch_size, vocab_size)
        teacher_probs = torch.rand(batch_size, vocab_size)
        
        student_probs = student_probs / student_probs.sum(dim=-1, keepdim=True)
        teacher_probs = teacher_probs / teacher_probs.sum(dim=-1, keepdim=True)
        
        reward = computer.compute_reward(student_probs, teacher_probs)
        
        assert reward.shape == (batch_size, vocab_size)
        assert torch.isfinite(reward).all()
        assert not torch.isnan(reward).any()
        assert not torch.isinf(reward).any()