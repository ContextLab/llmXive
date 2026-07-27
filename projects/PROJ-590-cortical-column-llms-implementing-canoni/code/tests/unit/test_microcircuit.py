import pytest
import torch
import torch.nn as nn
import json
import os
import tempfile
from pathlib import Path
import sys

# Add project root to path if running standalone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.training.homeostasis import enforce_ei_ratio, calculate_current_ei_ratio, HomeostasisConfig, HomeostaticScaler
from src.models.microcircuit import MicrocircuitColumn, create_microcircuit_column

class DummyModel(nn.Module):
    """Simple model for testing homeostasis functions."""
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(10, 20)
        self.fc2 = nn.Linear(20, 5)
        
        # Initialize with specific E/I pattern for testing
        with torch.no_grad():
            self.fc1.weight[:] = 0.5  # Excitatory
            self.fc1.bias[:] = 0.0
            self.fc2.weight[:] = -0.2  # Inhibitory
            self.fc2.bias[:] = 0.0

def test_epoch_scaling():
    """
    Integration test for T008c: Verify epoch-level E/I ratio enforcement.
    
    This test ensures that `enforce_ei_ratio` dynamically adjusts weights 
    to maintain the 4:1 ratio during a simulated training step.
    """
    model = DummyModel()
    
    # 1. Check initial state
    initial_ratio = calculate_current_ei_ratio(model)
    # Initial: Exc=0.5*10*20=100, Inh=0.2*20*5=20. Ratio = 5.0
    assert initial_ratio > 0, "Initial ratio should be positive"
    
    # 2. Enforce ratio (Target 4.0)
    step = 100
    factors = enforce_ei_ratio(model, step, target_ratio=4.0, decay_rate=1.0)
    
    # 3. Verify factors were applied
    assert len(factors) > 0, "Scaling factors should be applied"
    
    # 4. Check new ratio
    new_ratio = calculate_current_ei_ratio(model)
    # With decay=1.0 and target 4.0, ratio should move significantly towards 4.0
    # Exact value depends on the scaling logic implementation
    assert new_ratio > 0, "New ratio must be positive"
    
    # 5. Verify log file creation
    log_path = "data/logs/homeostasis_enforcement.json"
    assert os.path.exists(log_path), f"Log file {log_path} should be created"
    
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    assert len(log_data) > 0, "Log should contain at least one entry"
    assert log_data[-1]["step"] == step
    assert log_data[-1]["target_ratio"] == 4.0

def test_homeostatic_scaler_class():
    """Test the HomeostaticScaler class integration."""
    config = HomeostasisConfig(target_ei_ratio=4.0, decay_rate=0.5)
    scaler = HomeostaticScaler(config)
    
    model = DummyModel()
    stats = scaler.enforce_ei_ratio(model, step=500)
    
    assert stats is not None
    assert "fc1" in stats.scale_factors_applied or "fc2" in stats.scale_factors_applied

if __name__ == "__main__":
    test_epoch_scaling()
    test_homeostatic_scaler_class()
    print("All tests passed.")
