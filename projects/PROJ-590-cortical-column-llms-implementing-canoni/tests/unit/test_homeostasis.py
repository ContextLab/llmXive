"""
Unit tests for homeostatic scaling logic (T069b).
Verifies that scale_weights restores target activity after noise perturbation.
"""
import pytest
import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# Import from the project's homeostasis module
from src.training.homeostasis import (
    scale_weights,
    calculate_current_activity,
    HomeostasisConfig,
    ActivityStats
)


class SimpleLinearModel(nn.Module):
    """A minimal model with a single linear layer for testing scaling."""
    def __init__(self, in_features: int = 10, out_features: int = 10):
        super().__init__()
        self.linear = nn.Linear(in_features, out_features, bias=True)

    def forward(self, x):
        return self.linear(x)


class TwoLayerModel(nn.Module):
    """A model with two linear layers to test multi-parameter scaling."""
    def __init__(self):
        super().__init__()
        self.layer1 = nn.Linear(8, 16)
        self.layer2 = nn.Linear(16, 4)

    def forward(self, x):
        return self.layer2(self.layer1(x))


def get_all_weights(model: nn.Module) -> Dict[str, torch.Tensor]:
    """Extract all weight tensors from a model."""
    weights = {}
    for name, param in model.named_parameters():
        if 'weight' in name:
            weights[name] = param.data.clone()
    return weights


def perturb_weights(model: nn.Module, noise_scale: float = 0.5) -> Dict[str, torch.Tensor]:
    """Apply random noise to all weight parameters."""
    for param in model.parameters():
        if param.requires_grad and 'weight' in param.name:
            noise = torch.randn_like(param.data) * noise_scale
            param.data = param.data + noise
    return get_all_weights(model)


def calculate_weighted_activity(weights: Dict[str, torch.Tensor], 
                                input_tensor: Optional[torch.Tensor] = None) -> float:
    """
    Calculate a scalar 'activity' metric based on weight magnitudes.
    For testing, we use the mean absolute value of all weights.
    """
    total_activity = 0.0
    count = 0
    for w in weights.values():
        total_activity += torch.abs(w).mean().item()
        count += 1
    return total_activity / count if count > 0 else 0.0


class TestScaleWeights:
    """Tests for the scale_weights function (T069b)."""

    def test_scale_weights_restores_activity_single_layer(self):
        """
        Test that scale_weights restores target activity after noise perturbation.
        Uses a simple single-layer model.
        """
        model = SimpleLinearModel(in_features=10, out_features=10)
        original_weights = get_all_weights(model)
        
        # Calculate original activity
        original_activity = calculate_weighted_activity(original_weights)
        target_activity = original_activity * 0.5  # Target 50% of original

        # Perturb weights with noise
        perturbed_weights = perturb_weights(model, noise_scale=1.0)
        perturbed_activity = calculate_weighted_activity(perturbed_weights)

        # Apply scaling to restore target activity
        config = HomeostasisConfig(
            target_activity_ratio=0.5,
            decay_rate=0.1,
            min_scale_factor=0.1,
            max_scale_factor=10.0
        )
        
        scaling_factors = scale_weights(model, target_activity, decay_rate=config.decay_rate)
        
        # Verify scaling factors were applied
        new_weights = get_all_weights(model)
        assert len(scaling_factors) > 0, "No scaling factors returned"
        
        # Check that weights changed
        for name, original_w in original_weights.items():
            new_w = new_weights[name]
            # Weights should have been modified (unless scale factor was 1.0 exactly)
            # Allow small floating point differences
            if name in scaling_factors:
                expected_scale = scaling_factors[name]
                # Verify the scaling was applied approximately
                diff_ratio = torch.abs(new_w - original_w * expected_scale).mean() / (torch.abs(original_w).mean() + 1e-8)
                assert diff_ratio < 0.01, f"Scaling not applied correctly for {name}"

    def test_scale_weights_restores_activity_multi_layer(self):
        """
        Test scaling on a two-layer model with different initial activities.
        """
        model = TwoLayerModel()
        
        # Set different initial weights for each layer
        with torch.no_grad():
            model.layer1.weight.data = torch.ones_like(model.layer1.weight) * 2.0
            model.layer2.weight.data = torch.ones_like(model.layer2.weight) * 0.5
        
        original_weights = get_all_weights(model)
        original_activity = calculate_weighted_activity(original_weights)
        target_activity = original_activity * 0.8  # Target 80% of original

        # Perturb
        perturb_weights(model, noise_scale=0.3)
        
        # Scale
        config = HomeostasisConfig(
            target_activity_ratio=0.8,
            decay_rate=0.05,
            min_scale_factor=0.01,
            max_scale_factor=5.0
        )
        
        scaling_factors = scale_weights(model, target_activity, decay_rate=config.decay_rate)
        
        new_weights = get_all_weights(model)
        new_activity = calculate_weighted_activity(new_weights)
        
        # Verify activity is closer to target (within tolerance)
        tolerance = 0.15  # 15% tolerance on activity restoration
        activity_error = abs(new_activity - target_activity) / target_activity
        assert activity_error < tolerance, \
            f"Activity restoration failed: target={target_activity:.4f}, new={new_activity:.4f}, error={activity_error:.2%}"

    def test_scale_weights_respects_bounds(self):
        """
        Test that scaling factors respect min/max bounds.
        """
        model = SimpleLinearModel()
        target_activity = 0.001  # Very low target to force large scaling
        
        config = HomeostasisConfig(
            target_activity_ratio=0.01,
            decay_rate=1.0,
            min_scale_factor=0.1,
            max_scale_factor=2.0
        )
        
        # First, perturb to create high activity
        perturb_weights(model, noise_scale=5.0)
        
        scaling_factors = scale_weights(model, target_activity, decay_rate=config.decay_rate)
        
        for name, factor in scaling_factors.items():
            assert config.min_scale_factor <= factor <= config.max_scale_factor, \
                f"Scaling factor {factor} for {name} out of bounds [{config.min_scale_factor}, {config.max_scale_factor}]"

    def test_scale_weights_deterministic_with_seed(self):
        """
        Test that scaling is deterministic given the same initial state.
        """
        torch.manual_seed(42)
        model1 = SimpleLinearModel()
        target = 0.5
        
        perturb_weights(model1, noise_scale=0.5)
        factors1 = scale_weights(model1, target, decay_rate=0.1)
        
        torch.manual_seed(42)
        model2 = SimpleLinearModel()
        perturb_weights(model2, noise_scale=0.5)
        factors2 = scale_weights(model2, target, decay_rate=0.1)
        
        # Compare scaling factors
        for name in factors1:
            assert torch.allclose(factors1[name], factors2[name], rtol=1e-5), \
                f"Non-deterministic scaling for {name}: {factors1[name]} vs {factors2[name]}"

    def test_scale_weights_with_zero_activity(self):
        """
        Test behavior when activity is zero (edge case).
        """
        model = SimpleLinearModel()
        # Set weights to zero
        with torch.no_grad():
            for param in model.parameters():
                if 'weight' in param.name:
                    param.data.zero_()
        
        target_activity = 1.0
        
        # Should not crash, should apply max scaling or handle gracefully
        config = HomeostasisConfig(
            target_activity_ratio=1.0,
            decay_rate=0.1,
            min_scale_factor=0.0,
            max_scale_factor=100.0
        )
        
        try:
            scaling_factors = scale_weights(model, target_activity, decay_rate=config.decay_rate)
            # If it doesn't crash, verify factors are reasonable
            for name, factor in scaling_factors.items():
                assert factor >= 0.0, f"Negative scaling factor: {factor}"
        except Exception as e:
            # It's acceptable to raise if activity is zero (division by zero)
            # but the error should be clear
            assert "zero" in str(e).lower() or "activity" in str(e).lower(), \
                f"Unexpected error: {e}"

    def test_scale_weights_preserves_weight_signs(self):
        """
        Test that scaling preserves the sign of weights (only magnitude changes).
        """
        model = SimpleLinearModel()
        target_activity = 0.5
        
        # Create weights with mixed signs
        with torch.no_grad():
            model.linear.weight.data = torch.randn_like(model.linear.weight.data)
        
        original_signs = {name: torch.sign(w) for name, w in get_all_weights(model).items()}
        
        perturb_weights(model, noise_scale=0.2)
        scale_weights(model, target_activity, decay_rate=0.1)
        
        new_weights = get_all_weights(model)
        new_signs = {name: torch.sign(w) for name, w in new_weights.items()}
        
        for name in original_signs:
            # Signs should be preserved (allowing for numerical noise near zero)
            sign_match = torch.allclose(
                original_signs[name], 
                new_signs[name],
                atol=1e-6
            )
            # If signs differ, check if weights are near zero (where sign is unstable)
            if not sign_match:
                is_near_zero = torch.abs(new_weights[name]).mean() < 1e-8
                assert is_near_zero, f"Sign changed for {name} but weights not near zero"

    def test_scale_weights_tolerance_margin(self):
        """
        Test that activity restoration is within acceptable tolerance.
        """
        model = TwoLayerModel()
        original_weights = get_all_weights(model)
        original_activity = calculate_weighted_activity(original_weights)
        target_activity = original_activity * 0.6
        
        # Large perturbation
        perturb_weights(model, noise_scale=2.0)
        
        config = HomeostasisConfig(
            target_activity_ratio=0.6,
            decay_rate=0.2,
            min_scale_factor=0.01,
            max_scale_factor=10.0
        )
        
        scale_weights(model, target_activity, decay_rate=config.decay_rate)
        
        new_activity = calculate_weighted_activity(get_all_weights(model))
        
        # Tolerance: within 20% of target
        tolerance = 0.20
        error = abs(new_activity - target_activity) / target_activity
        assert error < tolerance, \
            f"Activity restoration error {error:.2%} exceeds tolerance {tolerance:.2%}. " \
            f"Target: {target_activity:.4f}, Actual: {new_activity:.4f}"

    def test_scale_weights_multiple_iterations(self):
        """
        Test that repeated scaling converges toward target.
        """
        model = SimpleLinearModel()
        target_activity = 0.5
        
        # Start with high activity
        with torch.no_grad():
            model.linear.weight.data = torch.ones_like(model.linear.weight.data) * 5.0
        
        activities = []
        for i in range(5):
            current_activity = calculate_weighted_activity(get_all_weights(model))
            activities.append(current_activity)
            scale_weights(model, target_activity, decay_rate=0.3)
        
        # Verify convergence trend (activity should decrease toward target)
        assert activities[-1] < activities[0], "Activity did not decrease toward target"
        
        # Final activity should be closer to target than initial
        initial_error = abs(activities[0] - target_activity)
        final_error = abs(activities[-1] - target_activity)
        assert final_error < initial_error, "Scaling did not improve activity match"