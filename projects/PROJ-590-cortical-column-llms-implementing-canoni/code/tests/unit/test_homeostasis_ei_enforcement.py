import pytest
import torch
import torch.nn as nn
import os
import tempfile
from pathlib import Path

from src.training.homeostasis import (
    HomeostasisConfig,
    enforce_ei_ratio,
    identify_excitatory_inhibitory_params,
    calculate_current_ei_ratio,
    scale_weights,
    verify_ei_balance,
    HomeostaticScaler
)


class SimpleModel(nn.Module):
    """A simple model with distinct excitatory and inhibitory-like layers for testing."""
    def __init__(self):
        super().__init__()
        # Simulate excitatory layer (L23-like)
        self.exc_layer = nn.Linear(10, 5)
        # Simulate inhibitory layer (L4-like)
        self.inh_layer = nn.Linear(5, 2)
        
        # Initialize with known values
        with torch.no_grad():
            self.exc_layer.weight.fill_(1.0)
            self.inh_layer.weight.fill_(0.5)

class TestEIEnforcementPerBatch:
    """Tests for T010c: Dynamic E/I ratio enforcement per batch."""

    def test_enforce_ei_ratio_updates_weights(self):
        """Test that enforce_ei_ratio actually modifies model weights."""
        model = SimpleModel()
        config = HomeostasisConfig(
            target_ei_ratio=2.0,
            enforce_per_batch=True,
            scaling_decay_rate=1.0  # Immediate application
        )
        
        # Initial weights
        initial_exc_norm = torch.norm(model.exc_layer.weight).item()
        initial_inh_norm = torch.norm(model.inh_layer.weight).item()
        
        # Enforce ratio
        result = enforce_ei_ratio(model, config, step=1)
        
        # Check that weights changed
        new_exc_norm = torch.norm(model.exc_layer.weight).item()
        assert new_exc_norm != initial_exc_norm, "Excitatory weights should have changed"
        
        # Check result contains expected keys
        assert "effective_scale" in result
        assert "current_ratio" in result

    def test_enforce_per_batch_flag(self):
        """Test that enforce_per_batch=False skips scaling."""
        model = SimpleModel()
        config = HomeostasisConfig(
            target_ei_ratio=2.0,
            enforce_per_batch=False
        )
        
        initial_exc_norm = torch.norm(model.exc_layer.weight).item()
        
        result = enforce_ei_ratio(model, config, step=1)
        
        # Weights should not change
        new_exc_norm = torch.norm(model.exc_layer.weight).item()
        assert new_exc_norm == initial_exc_norm, "Weights should not change when enforce_per_batch=False"
        assert result == {}, "Result should be empty dict when skipped"

    def test_target_ratio_enforcement(self):
        """Test that the ratio moves towards the target."""
        model = SimpleModel()
        # Initial: Exc=1.0, Inh=0.5 -> Ratio = 2.0 (already at target if target=2.0)
        # Let's change target to 1.0 to see scaling
        config = HomeostasisConfig(
            target_ei_ratio=1.0,
            enforce_per_batch=True,
            scaling_decay_rate=1.0
        )
        
        # Force a known ratio
        with torch.no_grad():
            model.exc_layer.weight.fill_(2.0)
            model.inh_layer.weight.fill_(1.0)
        
        initial_ratio = calculate_current_ei_ratio(
            identify_excitatory_inhibitory_params(model)[0],
            identify_excitatory_inhibitory_params(model)[1]
        )
        
        assert initial_ratio == 2.0, "Setup ratio should be 2.0"
        
        # Enforce target 1.0
        enforce_ei_ratio(model, config, step=1)
        
        new_ratio = calculate_current_ei_ratio(
            identify_excitatory_inhibitory_params(model)[0],
            identify_excitatory_inhibitory_params(model)[1]
        )
        
        # Should be closer to 1.0
        assert new_ratio < initial_ratio, "Ratio should decrease towards target"
        assert new_ratio >= 1.0, "Ratio should not undershoot significantly with decay=1.0"

    def test_scale_clamping(self):
        """Test that scale factors are clamped to min/max."""
        model = SimpleModel()
        config = HomeostasisConfig(
            target_ei_ratio=100.0,  # Extreme target
            enforce_per_batch=True,
            scaling_decay_rate=1.0,
            min_scale_factor=0.1,
            max_scale_factor=10.0
        )
        
        # Current ratio is 2.0 (1.0 / 0.5)
        # Target is 100.0 -> Scale factor = 50.0
        # Should be clamped to 10.0
        
        initial_exc_norm = torch.norm(model.exc_layer.weight).item()
        
        result = enforce_ei_ratio(model, config, step=1)
        
        new_exc_norm = torch.norm(model.exc_layer.weight).item()
        actual_scale = new_exc_norm / initial_exc_norm
        
        assert actual_scale <= 10.0, f"Scale factor {actual_scale} exceeded max clamp"

    def test_batch_activity_override(self):
        """Test that providing batch_activity overrides parameter-based estimation."""
        model = SimpleModel()
        config = HomeostasisConfig(
            target_ei_ratio=1.0,
            enforce_per_batch=True,
            scaling_decay_rate=1.0
        )
        
        # Provide artificial batch activity
        batch_activity = {
            "exc_layer": 10.0,
            "inh_layer": 5.0
        }
        # Ratio = 2.0 -> Target 1.0 -> Scale down excitation
        
        initial_exc_norm = torch.norm(model.exc_layer.weight).item()
        
        enforce_ei_ratio(model, config, step=1, batch_activity=batch_activity)
        
        new_exc_norm = torch.norm(model.exc_layer.weight).item()
        assert new_exc_norm < initial_exc_norm, "Excitatory weights should decrease to match batch activity ratio"

    def test_verify_ei_balance_tolerance(self):
        """Test the verification function."""
        model = SimpleModel()
        # Ratio is 2.0
        
        # Target 2.0, tolerance 0.1 -> Should pass
        assert verify_ei_balance(model, target_ratio=2.0, tolerance=0.1)
        
        # Target 1.0, tolerance 0.1 -> Should fail
        assert not verify_ei_balance(model, target_ratio=1.0, tolerance=0.1)

class TestHomeostaticScaler:
    """Tests for the stateful scaler."""

    def test_scaler_accumulates_activity(self):
        """Test that the scaler tracks activity over steps."""
        config = HomeostasisConfig(activity_window=3)
        scaler = HomeostaticScaler(config)
        
        scaler.update_activity(exc_activity=10.0, inh_activity=5.0)
        scaler.update_activity(exc_activity=20.0, inh_activity=10.0)
        
        avg_exc, avg_inh = scaler.get_average_activity()
        
        assert avg_exc == 15.0
        assert avg_inh == 7.5

    def test_scaler_window_limit(self):
        """Test that old activity is dropped when window is full."""
        config = HomeostasisConfig(activity_window=2)
        scaler = HomeostaticScaler(config)
        
        scaler.update_activity(10.0, 5.0)
        scaler.update_activity(20.0, 10.0)
        scaler.update_activity(30.0, 15.0)  # Should drop first entry
        
        avg_exc, avg_inh = scaler.get_average_activity()
        
        # Average of 2nd and 3rd
        assert avg_exc == 25.0
        assert avg_inh == 12.5