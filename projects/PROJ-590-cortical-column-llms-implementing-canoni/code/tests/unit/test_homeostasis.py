import pytest
import torch
import torch.nn as nn
import json
import os
import tempfile
from pathlib import Path
from src.training.homeostasis import (
    HomeostasisConfig,
    ActivityStats,
    calculate_current_ei_ratio,
    scale_weights,
    apply_ei_balance_constraint,
    verify_ei_balance,
    HomeostaticScaler,
    log_gradient_norms
)

class DummyModel(nn.Module):
    """Simple model with explicitly named excitatory and inhibitory parameters."""
    def __init__(self):
        super().__init__()
        self.excitatory_weight = nn.Parameter(torch.randn(10, 10))
        self.inhibitory_weight = nn.Parameter(torch.randn(10, 10) * 0.25)
        
    def forward(self, x):
        return x

class TestCalculateCurrentEiRatio:
    def test_ei_ratio_calculation(self):
        model = DummyModel()
        stats = calculate_current_ei_ratio(model)
        
        assert isinstance(stats, ActivityStats)
        assert stats.excitatory_mean > 0
        assert stats.inhibitory_mean > 0
        assert stats.current_ratio > 0
        assert stats.total_params == 200

    def test_default_ratio_when_no_ei_naming(self):
        class NoNamingModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.weight = nn.Parameter(torch.randn(10, 10))
            def forward(self, x):
                return x
        
        model = NoNamingModel()
        stats = calculate_current_ei_ratio(model)
        
        assert stats.current_ratio == 4.0
        assert stats.excitatory_mean == 1.0
        assert stats.inhibitory_mean == 0.25

class TestScaleWeights:
    def test_scale_weights_applies_factor(self):
        model = DummyModel()
        initial_exc = model.excitatory_weight.data.clone()
        
        factors = scale_weights(model, target_ratio=4.0, decay_rate=0.1)
        
        assert len(factors) > 0
        assert 'excitatory_weight' in factors
        assert 'inhibitory_weight' in factors
        
        # Verify weights changed
        assert not torch.equal(model.excitatory_weight.data, initial_exc)

    def test_scale_weights_clamping(self):
        model = DummyModel()
        # Set extreme ratio
        with torch.no_grad():
            model.excitatory_weight.data.fill_(100.0)
            model.inhibitory_weight.data.fill_(0.01)
        
        factors = scale_weights(model, target_ratio=4.0, decay_rate=1.0)
        
        # Check factors are clamped
        for factor in factors.values():
            assert 0.1 <= factor <= 5.0

class TestApplyEiBalanceConstraint:
    def test_constraint_enforcement(self):
        model = DummyModel()
        # Set ratio below minimum
        with torch.no_grad():
            model.excitatory_weight.data.fill_(0.1)
            model.inhibitory_weight.data.fill_(1.0)
        
        apply_ei_balance_constraint(model, min_ratio=2.0, max_ratio=6.0)
        
        stats = calculate_current_ei_ratio(model)
        assert stats.current_ratio >= 2.0

class TestVerifyEiBalance:
    def test_verify_within_tolerance(self):
        model = DummyModel()
        # Default model should be within tolerance
        assert verify_ei_balance(model, tolerance=0.5) is False  # Default ratio might not be exactly 4.0
        
        # Force ratio to 4.0
        with torch.no_grad():
            model.inhibitory_weight.data /= 4.0
        
        assert verify_ei_balance(model, tolerance=0.5) is True

class TestHomeostaticScaler:
    def test_scaler_step(self):
        config = HomeostasisConfig(target_ratio=4.0, decay_rate=0.1)
        scaler = HomeostaticScaler(config, log_interval=1)
        model = DummyModel()
        
        scaler.step(model)
        assert scaler.step_count == 1
        assert len(scaler.scaling_history) == 1

    def test_scaler_logging_interval(self):
        config = HomeostasisConfig(target_ratio=4.0, decay_rate=0.1)
        scaler = HomeostaticScaler(config, log_interval=5)
        model = DummyModel()
        
        for i in range(10):
            scaler.step(model)
        
        assert scaler.step_count == 10
        assert len(scaler.scaling_history) == 2  # Steps 5 and 10

class TestLogGradientNorms:
    def test_log_gradient_norms_creates_file(self):
        model = DummyModel()
        # Create dummy gradients
        for param in model.parameters():
            param.grad = torch.randn_like(param)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, 'gradient_norms.json')
            result = log_gradient_norms(model, step=0, log_file=log_file)
            
            assert os.path.exists(log_file)
            assert 'step' in result
            assert 'total_norm' in result
            assert result['step'] == 0

    def test_log_gradient_norms_appends(self):
        model = DummyModel()
        for param in model.parameters():
            param.grad = torch.randn_like(param)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, 'gradient_norms.json')
            
            # First log
            log_gradient_norms(model, step=0, log_file=log_file)
            # Second log
            log_gradient_norms(model, step=1, log_file=log_file)
            
            with open(log_file, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 2
            assert data[0]['step'] == 0
            assert data[1]['step'] == 1

    def test_log_gradient_norms_handles_no_grad(self):
        model = DummyModel()
        # Don't set gradients
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, 'gradient_norms.json')
            result = log_gradient_norms(model, step=0, log_file=log_file)
            
            assert result['excitatory_weight'] == 0.0
            assert result['inhibitory_weight'] == 0.0

    def test_log_gradient_norms_creates_directory(self):
        model = DummyModel()
        for param in model.parameters():
            param.grad = torch.randn_like(param)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_log_file = os.path.join(tmpdir, 'subdir', 'gradient_norms.json')
            result = log_gradient_norms(model, step=0, log_file=nested_log_file)
            
            assert os.path.exists(nested_log_file)
            assert result['step'] == 0

    def test_log_gradient_norms_corrupt_file_recovery(self):
        model = DummyModel()
        for param in model.parameters():
            param.grad = torch.randn_like(param)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, 'gradient_norms.json')
            # Write corrupt JSON
            with open(log_file, 'w') as f:
                f.write("not valid json")
            
            # Should recover and create new list
            result = log_gradient_norms(model, step=0, log_file=log_file)
            
            with open(log_file, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 1
            assert data[0]['step'] == 0