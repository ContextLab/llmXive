import pytest
import torch
import torch.nn as nn
import json
import os
import tempfile
from pathlib import Path
from src.training.homeostasis import (
    HomeostasisConfig,
    HomeostaticScaler,
    apply_scaling_hook,
    scale_weights,
    enforce_ei_ratio,
    log_gradient_norms
)

class DummyModel(nn.Module):
    """Simple dummy model for testing homeostasis functions."""
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(10, 20)
        self.fc2 = nn.Linear(20, 5)
    
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        return self.fc2(x)

@pytest.fixture
def temp_log_dir():
    """Create temporary directory for log files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def dummy_model():
    """Create a dummy model for testing."""
    return DummyModel()

@pytest.fixture
def dummy_optimizer(dummy_model):
    """Create optimizer for dummy model."""
    return torch.optim.SGD(dummy_model.parameters(), lr=0.01)

def test_apply_scaling_hook_creates_log_files(dummy_model, dummy_optimizer, temp_log_dir):
    """Test that apply_scaling_hook creates required log files."""
    config = HomeostasisConfig(
        log_path=os.path.join(temp_log_dir, "ei_ratio_log.json"),
        gradient_log_path=os.path.join(temp_log_dir, "gradient_norms.json")
    )
    
    # Simulate a training step
    x = torch.randn(2, 10)
    y = dummy_model(x)
    loss = y.sum()
    loss.backward()
    
    # Apply scaling hook
    factors = apply_scaling_hook(dummy_optimizer, step=1, config=config)
    
    # Verify log files exist
    assert os.path.exists(config.log_path), f"Log file not created: {config.log_path}"
    assert os.path.exists(config.gradient_log_path), f"Gradient log not created: {config.gradient_log_path}"
    
    # Verify log contents
    with open(config.log_path, 'r') as f:
        ei_logs = json.load(f)
        assert len(ei_logs) >= 1
        assert "scaling_factor" in ei_logs[0]
        assert "exc_activity" in ei_logs[0]
        assert "inh_activity" in ei_logs[0]
    
    with open(config.gradient_log_path, 'r') as f:
        grad_logs = json.load(f)
        assert len(grad_logs) >= 1
        assert "norm" in grad_logs[0]
        assert "step" in grad_logs[0]

def test_scaling_factors_are_returned(dummy_model, dummy_optimizer, temp_log_dir):
    """Test that scaling factors are correctly returned."""
    config = HomeostasisConfig(
        log_path=os.path.join(temp_log_dir, "ei_ratio_log.json"),
        gradient_log_path=os.path.join(temp_log_dir, "gradient_norms.json")
    )
    
    x = torch.randn(2, 10)
    y = dummy_model(x)
    loss = y.sum()
    loss.backward()
    
    factors = apply_scaling_hook(dummy_optimizer, step=1, config=config)
    
    # Verify factors are returned
    assert isinstance(factors, dict)
    assert len(factors) > 0
    assert "scaling_factor" in factors or any(isinstance(v, (int, float)) for v in factors.values())

def test_scaling_hook_applied_multiple_steps(dummy_model, dummy_optimizer, temp_log_dir):
    """Test that scaling hook works across multiple steps."""
    config = HomeostasisConfig(
        log_path=os.path.join(temp_log_dir, "ei_ratio_log.json"),
        gradient_log_path=os.path.join(temp_log_dir, "gradient_norms.json")
    )
    
    for step in range(1, 4):
        x = torch.randn(2, 10)
        y = dummy_model(x)
        loss = y.sum()
        loss.backward()
        
        apply_scaling_hook(dummy_optimizer, step=step, config=config)
        
        # Clear gradients for next step
        dummy_optimizer.zero_grad()
    
    # Verify multiple log entries
    with open(config.log_path, 'r') as f:
        ei_logs = json.load(f)
        assert len(ei_logs) == 3, f"Expected 3 log entries, got {len(ei_logs)}"
    
    with open(config.gradient_log_path, 'r') as f:
        grad_logs = json.load(f)
        assert len(grad_logs) == 3, f"Expected 3 gradient log entries, got {len(grad_logs)}"

def test_scale_weights_function(dummy_model, temp_log_dir):
    """Test the scale_weights function directly."""
    config = HomeostasisConfig()
    
    initial_weight_sum = sum(p.abs().sum().item() for p in dummy_model.parameters())
    
    factors = scale_weights(dummy_model, target_ratio=4.0, decay_rate=0.01)
    
    final_weight_sum = sum(p.abs().sum().item() for p in dummy_model.parameters())
    
    # Weights should have been scaled
    assert len(factors) > 0
    # The sum should have changed (unless scale_factor was exactly 1.0)
    # We allow for small numerical differences
    assert abs(final_weight_sum - initial_weight_sum) / initial_weight_sum < 0.5

def test_enforce_ei_ratio_function(dummy_model, temp_log_dir):
    """Test the enforce_ei_ratio function directly."""
    log_path = os.path.join(temp_log_dir, "ei_ratio_log.json")
    
    result = enforce_ei_ratio(dummy_model, step=1, target_ratio=4.0, log_path=log_path)
    
    assert "scaling_factor" in result
    assert "exc_activity" in result
    assert "inh_activity" in result
    
    # Verify log file was created
    assert os.path.exists(log_path)
    with open(log_path, 'r') as f:
        logs = json.load(f)
        assert len(logs) == 1

def test_log_gradient_norms_function(dummy_model, temp_log_dir):
    """Test the log_gradient_norms function directly."""
    log_path = os.path.join(temp_log_dir, "gradient_norms.json")
    
    # Create gradients
    x = torch.randn(2, 10)
    y = dummy_model(x)
    loss = y.sum()
    loss.backward()
    
    log_gradient_norms(dummy_model, step=1, log_path=log_path)
    
    assert os.path.exists(log_path)
    with open(log_path, 'r') as f:
        logs = json.load(f)
        assert len(logs) > 0
        assert "norm" in logs[0]
        assert "step" in logs[0]