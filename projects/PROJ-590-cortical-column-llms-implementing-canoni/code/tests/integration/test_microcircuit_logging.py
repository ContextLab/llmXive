"""
Integration test for T011d: Microcircuit Gradient Logging.

Verifies that the microcircuit runner produces the required artifact:
data/logs/gradient_norms_microcircuit.json
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
import sys
import torch

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.experiments.microcircuit_runner import MicrocircuitRunner, MicrocircuitConfig
from src.training.homeostasis import log_gradient_norms

class TestMicrocircuitLogging:
    """Tests for T011d implementation."""

    def test_gradient_log_file_creation(self, tmp_path):
        """
        Test that run_with_logging creates the gradient_norms_microcircuit.json file.
        """
        # Setup temp paths
        log_path = tmp_path / "gradient_norms_microcircuit.json"
        metrics_path = tmp_path / "microcircuit_metrics.json"

        config = MicrocircuitConfig(
            hidden_dim=32, # Smaller for speed
            num_layers=2,
            neurons_per_layer=64,
            epochs=2,      # Minimal epochs for test
            learning_rate=1e-3,
            seed=42,
            gradient_log_path=str(log_path),
            metrics_path=str(metrics_path)
        )

        runner = MicrocircuitRunner(config)
        
        # Run training
        result = runner.run_with_logging()

        # Verify artifact existence
        assert log_path.exists(), f"Gradient log file not created at {log_path}"
        assert metrics_path.exists(), f"Metrics file not created at {metrics_path}"

        # Verify content schema
        with open(log_path, 'r') as f:
            log_data = json.load(f)
        
        assert isinstance(log_data, list), "Log data must be a list of entries"
        assert len(log_data) > 0, "Log data must not be empty"
        
        # Check schema of first entry
        entry = log_data[0]
        assert "step" in entry, "Entry must have 'step'"
        assert "norm" in entry, "Entry must have 'norm'"
        assert isinstance(entry["norm"], float), "Norm must be a float"

        # Verify metrics schema
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        assert "train_mae" in metrics
        assert "test_mae" in metrics
        assert "total_time" in metrics

    def test_log_gradient_norms_function_directly(self, tmp_path):
        """
        Test the underlying log_gradient_norms function used by the runner.
        """
        from src.models.hybrid_network import create_hybrid_network
        
        # Create a small model
        model = create_hybrid_network(input_dim=10, hidden_dim=16, num_layers=2, neurons_per_layer=32)
        
        log_path = tmp_path / "direct_test.json"
        
        # Perform a dummy backward pass to generate gradients
        x = torch.randn(5, 10)
        y = model(x)
        loss = y.sum()
        loss.backward()
        
        # Log
        log_gradient_norms(model, step=0, output_path=str(log_path))
        
        assert log_path.exists()
        with open(log_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["step"] == 0
        assert "norm" in data[0]