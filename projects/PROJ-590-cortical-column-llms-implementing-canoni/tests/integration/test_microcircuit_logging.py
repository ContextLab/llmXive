import json
import os
import tempfile
import pytest
from pathlib import Path
import sys
import torch
import torch.nn as nn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.experiments.microcircuit_runner import MicrocircuitRunner, MicrocircuitConfig
from src.training.homeostasis import log_gradient_norms

class TestMicrocircuitLogging:
    """Test that microcircuit training produces gradient logs."""

    @pytest.fixture
    def temp_log_dir(self, tmp_path):
        """Create a temporary directory for logs."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        return str(log_dir)

    def test_run_with_logging_creates_gradient_file(self, temp_log_dir):
        """Test that run_with_logging creates gradient_norms_microcircuit.json."""
        # Create a minimal config for fast testing
        config = MicrocircuitConfig(
            seed=42,
            hidden_dim=16,
            neurons_per_layer=32,
            num_columns=2,
            learning_rate=0.001,
            num_epochs=2,
            batch_size=8,
            use_homeostasis=True,
            target_ei_ratio=4.0,
            log_dir=temp_log_dir
        )

        runner = MicrocircuitRunner(config)
        result = runner.run_with_logging()

        # Verify the gradient log file was created
        expected_path = os.path.join(temp_log_dir, "gradient_norms_microcircuit.json")
        assert os.path.exists(expected_path), f"Gradient log file not created at {expected_path}"

        # Verify the file contains valid JSON with gradient data
        with open(expected_path, 'r') as f:
            log_data = json.load(f)

        assert isinstance(log_data, list), "Gradient log should be a list"
        assert len(log_data) > 0, "Gradient log should not be empty"

        # Check schema of log entries
        for entry in log_data:
            assert "step" in entry, "Each entry should have a 'step' field"
            assert "norm" in entry, "Each entry should have a 'norm' field"
            assert isinstance(entry["step"], int), "Step should be an integer"
            assert isinstance(entry["norm"], float), "Norm should be a float"

    def test_gradient_log_contains_expected_steps(self, temp_log_dir):
        """Test that gradient log contains entries for multiple training steps."""
        config = MicrocircuitConfig(
            seed=42,
            hidden_dim=16,
            neurons_per_layer=32,
            num_columns=2,
            learning_rate=0.001,
            num_epochs=2,
            batch_size=8,
            use_homeostasis=True,
            target_ei_ratio=4.0,
            log_dir=temp_log_dir
        )

        runner = MicrocircuitRunner(config)
        result = runner.run_with_logging()

        expected_path = os.path.join(temp_log_dir, "gradient_norms_microcircuit.json")
        with open(expected_path, 'r') as f:
            log_data = json.load(f)

        # With 2 epochs and 8 batch size, we should have multiple steps logged
        steps = [entry["step"] for entry in log_data]
        assert len(set(steps)) > 1, "Should have logged gradients at multiple steps"

        # Steps should be monotonically increasing
        for i in range(1, len(steps)):
            assert steps[i] >= steps[i-1], "Steps should be non-decreasing"

    def test_log_gradient_norms_function(self, temp_log_dir):
        """Test the log_gradient_norms function directly."""
        # Create a simple model
        model = nn.Sequential(
            nn.Linear(10, 20),
            nn.ReLU(),
            nn.Linear(20, 1)
        )

        # Create dummy input and output to trigger backward pass
        x = torch.randn(5, 10)
        y = torch.randn(5, 1)

        loss_fn = nn.MSELoss()
        loss = loss_fn(model(x), y)
        loss.backward()

        # Log gradients
        log_path = os.path.join(temp_log_dir, "test_gradients.json")
        norms = log_gradient_norms(model, 0, log_path=log_path)

        # Verify norms were calculated
        assert len(norms) > 0, "Should have logged at least one gradient norm"
        assert all(isinstance(n, float) for n in norms), "All norms should be floats"

        # Verify file was created
        assert os.path.exists(log_path), "Log file should be created"

        # Verify file contents
        with open(log_path, 'r') as f:
            data = json.load(f)

        assert isinstance(data, list), "Log should be a list"
        assert len(data) > 0, "Log should not be empty"