import pytest
import os
import json
import tempfile
import torch
import torch.nn as nn
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.baseline_transformer import create_baseline_transformer
from src.training.homeostasis import log_gradient_norms

class DummyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(10, 10)
    
    def forward(self, x):
        return self.linear(x)

@pytest.fixture
def temp_log_file(tmp_path):
    # We need to temporarily override the log path for testing
    # Since log_gradient_norms uses a hardcoded path, we will test by ensuring
    # the file is created at the expected location or mock the path.
    # For integration test, we assume the standard path or use a monkeypatch if needed.
    # However, the function writes to 'data/logs/gradient_norms.json' relative to CWD.
    # We will run the test in a temp directory context if possible, or just check existence.
    # To be safe for the integration test, we will check if the file is created in the project root.
    # But for isolation, let's patch the LOG_DIR constant if possible, or just accept the side effect.
    # Given the constraints, we will run it and check the file in the expected location.
    # We will create the directory if it doesn't exist to avoid errors.
    os.makedirs("data/logs", exist_ok=True)
    return "data/logs/gradient_norms.json"

def test_log_gradient_norms_creates_file(temp_log_file):
    model = DummyModel()
    step = 0
    
    # Remove file if exists
    if os.path.exists(temp_log_file):
        os.remove(temp_log_file)

    # We need a backward pass to have gradients
    x = torch.randn(5, 10)
    y = model(x)
    loss = y.sum()
    loss.backward()

    log_gradient_norms(model, step)

    assert os.path.exists(temp_log_file), "Gradient log file was not created."

def test_log_gradient_norms_appends(temp_log_file):
    model = DummyModel()
    
    # Clear file
    if os.path.exists(temp_log_file):
        os.remove(temp_log_file)

    # First log
    x = torch.randn(5, 10)
    y = model(x)
    loss = y.sum()
    loss.backward()
    log_gradient_norms(model, 1)

    # Second log (need new gradients)
    model.zero_grad()
    x2 = torch.randn(5, 10)
    y2 = model(x2)
    loss2 = y2.sum()
    loss2.backward()
    log_gradient_norms(model, 2)

    with open(temp_log_file, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 2, "File should contain 2 entries."
    assert data[0]['step'] == 1
    assert data[1]['step'] == 2

def test_log_gradient_norms_no_gradients(temp_log_file):
    model = DummyModel()
    
    # Remove file
    if os.path.exists(temp_log_file):
        os.remove(temp_log_file)

    # No backward pass, so no gradients
    x = torch.randn(5, 10)
    y = model(x)
    # No loss.backward()
    
    log_gradient_norms(model, 99)

    with open(temp_log_file, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert data[0]['step'] == 99
    # Norms should be 0 or empty depending on implementation
    # Our implementation sets 0.0 if no grad

def test_log_gradient_norms_with_real_model(temp_log_file):
    # Use the baseline transformer
    model = create_baseline_transformer(d_model=32, nhead=2, num_layers=1, dim_feedforward=64)
    model.train()

    # Clear file
    if os.path.exists(temp_log_file):
        os.remove(temp_log_file)

    # Forward/Backward
    x = torch.randn(2, 8, 32)
    y = model(x)
    loss = y.sum()
    loss.backward()

    log_gradient_norms(model, 100)

    with open(temp_log_file, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert data[0]['step'] == 100
    assert 'norms' in data[0]
    assert len(data[0]['norms']) > 0 # Should have logged some parameters