"""
Unit tests for the homeostasis module.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import torch
import numpy as np

from src.training.homeostasis import (
    HomeostasisConfig,
    ActivityStats,
    identify_excitatory_inhibitory_params,
    calculate_current_activity,
    scale_weights,
    enforce_ei_ratio,
    apply_ei_balance_constraint,
    verify_ei_balance,
    HomeostaticScaler,
    apply_scaling_hook,
    log_gradient_norms,
    verify_independence
)


class TestHomeostasisModule:
    """Test cases for homeostasis utilities."""

    @pytest.fixture
    def simple_model(self):
        """Create a simple test model."""
        class TestModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.linear1 = torch.nn.Linear(10, 20)
                self.linear2 = torch.nn.Linear(20, 5)
                self.inhibitory_layer = torch.nn.Linear(5, 2)

            def forward(self, x):
                x = torch.relu(self.linear1(x))
                x = torch.relu(self.linear2(x))
                return self.inhibitory_layer(x)

        return TestModel()

    @pytest.fixture
    def model_with_gradients(self, simple_model):
        """Create a model with computed gradients."""
        model = simple_model
        x = torch.randn(32, 10)
        y = torch.randn(32, 2)

        output = model(x)
        loss = torch.nn.functional.mse_loss(output, y)
        loss.backward()

        return model

    def test_identify_excitatory_inhibitory_params(self, simple_model):
        """Test identification of excitatory and inhibitory parameters."""
        exc, inh = identify_excitatory_inhibitory_params(simple_model)

        # Should find excitatory parameters
        assert len(exc) > 0
        assert "linear1.weight" in exc
        assert "linear2.weight" in exc

        # Should find inhibitory parameters
        assert len(inh) > 0
        assert "inhibitory_layer.weight" in inh

    def test_scale_weights_applies_scaling(self, model_with_gradients):
        """Test that scale_weights applies scaling factors correctly."""
        model = model_with_gradients
        initial_weights = {
            name: param.data.clone()
            for name, param in model.named_parameters()
        }

        # Apply scaling
        factors = scale_weights(model, target_ratio=4.0, decay_rate=0.1)

        # Check that weights were modified
        for name, param in model.named_parameters():
            if "inhib" not in name:
                assert not torch.allclose(
                    param.data,
                    initial_weights[name],
                    atol=1e-6
                ), f"Excitatory parameter {name} should have been scaled"

        # Check that scaling factors were returned
        assert len(factors) > 0

    def test_verify_ei_balance_within_tolerance(self, model_with_gradients):
        """Test E/I balance verification within tolerance."""
        # This should not raise and should return True or False
        # depending on current state
        result = verify_ei_balance(model_with_gradients, target_ratio=4.0, tolerance=0.5)
        assert isinstance(result, bool)

    def test_log_gradient_norms_creates_file(self, model_with_gradients, tmp_path):
        """Test that log_gradient_norms creates the output file."""
        output_file = tmp_path / "gradient_norms.json"

        log_gradient_norms(model_with_gradients, step=0, output_file=str(output_file))

        assert output_file.exists()

        # Check file content
        with open(output_file, 'r') as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["step"] == 0
        assert "norms" in data[0]
        assert isinstance(data[0]["norms"], dict)

    def test_log_gradient_norms_appends(self, model_with_gradients, tmp_path):
        """Test that log_gradient_norms appends to existing file."""
        output_file = tmp_path / "gradient_norms.json"

        # Log first step
        log_gradient_norms(model_with_gradients, step=0, output_file=str(output_file))

        # Log second step
        log_gradient_norms(model_with_gradients, step=1, output_file=str(output_file))

        with open(output_file, 'r') as f:
            data = json.load(f)

        assert len(data) == 2
        assert data[0]["step"] == 0
        assert data[1]["step"] == 1

    def test_log_gradient_norms_format(self, model_with_gradients, tmp_path):
        """Test that log_gradient_norms writes correct JSON format."""
        output_file = tmp_path / "gradient_norms.json"

        log_gradient_norms(model_with_gradients, step=5, output_file=str(output_file))

        with open(output_file, 'r') as f:
            content = f.read()

        # Check 2-space indentation
        assert "  " in content

        # Check trailing newline
        assert content.endswith('\n')

    def test_verify_independence_distinct_distributions(self):
        """Test verify_independence with clearly distinct distributions."""
        train_data = torch.randn(1000, 10)  # Standard normal
        test_data = torch.randn(1000, 10) * 5 + 10  # Different mean and std

        # Should return True for distinct distributions
        result = verify_independence(train_data, test_data)
        assert result is True

    def test_verify_independence_same_distribution_raises(self):
        """Test verify_independence raises on same distribution."""
        # Create identical distributions
        data = torch.randn(1000, 10)
        train_data = data[:500]
        test_data = data[500:]

        # Should raise ValueError for non-distinct distributions
        with pytest.raises(ValueError, match="not statistically distinct"):
            verify_independence(train_data, test_data)

    def test_homeostatic_scaler_registers_hooks(self, simple_model):
        """Test that HomeostaticScaler registers backward hooks."""
        config = HomeostasisConfig(
            target_activity=1.0,
            decay_rate=0.1,
            target_ei_ratio=4.0
        )

        scaler = HomeostaticScaler(simple_model, config)
        scaler.register_scaling_hook()

        assert len(scaler.handles) > 0

        # Cleanup should remove hooks
        scaler.cleanup()
        assert len(scaler.handles) == 0

    def test_apply_scaling_hook(self, simple_model):
        """Test apply_scaling_hook function."""
        scaler = apply_scaling_hook(simple_model, target_ratio=4.0, decay_rate=0.1)

        assert isinstance(scaler, HomeostaticScaler)
        assert len(scaler.handles) > 0

        scaler.cleanup()

    def test_scale_weights_with_no_gradients(self, simple_model):
        """Test scale_weights when no gradients are present."""
        # Ensure no gradients
        for param in simple_model.parameters():
            param.grad = None

        # Should not crash
        factors = scale_weights(simple_model, target_ratio=4.0, decay_rate=0.1)

        # Should return empty dict or only scale parameters with gradients
        assert isinstance(factors, dict)

    def test_log_gradient_norms_with_no_gradients(self, simple_model, tmp_path):
        """Test log_gradient_norms when no gradients are present."""
        output_file = tmp_path / "gradient_norms.json"

        # Ensure no gradients
        for param in simple_model.parameters():
            param.grad = None

        # Should not crash
        log_gradient_norms(simple_model, step=0, output_file=str(output_file))

        with open(output_file, 'r') as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["norms"] == {}  # Empty norms dict

    def test_log_gradient_norms_concurrent_safety(self, model_with_gradients, tmp_path):
        """Test that log_gradient_norms handles concurrent writes safely."""
        import threading
        import time

        output_file = tmp_path / "gradient_norms.json"

        def log_step(step):
            log_gradient_norms(model_with_gradients, step=step, output_file=str(output_file))

        threads = []
        for i in range(5):
            t = threading.Thread(target=log_step, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        with open(output_file, 'r') as f:
            data = json.load(f)

        # All steps should be logged (order may vary due to threading)
        steps_logged = {entry["step"] for entry in data}
        assert len(steps_logged) == 5
        assert steps_logged == {0, 1, 2, 3, 4}
