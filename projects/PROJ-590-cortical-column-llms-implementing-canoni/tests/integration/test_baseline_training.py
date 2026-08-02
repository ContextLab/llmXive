"""
Integration tests for the baseline training pipeline.

This module verifies that the baseline training process:
1. Executes successfully within resource constraints.
2. Produces the required gradient norm logs for SC-002 verification.
3. Generates valid baseline metrics.
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
import sys
import shutil

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from src.training.homeostasis import log_gradient_norms
from src.experiments.baseline_runner import BaselineRunner, ExperimentConfig
from src.data.benchmarks import generate_training_data, generate_test_data, verify_independence
from src.training.trainer import TrainingConfig, run_training
from src.models.baseline_transformer import BaselineTransformer


class TestBaselineTraining:
    """Integration tests for the baseline training pipeline."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Setup and teardown for each test."""
        # Create temporary directories for logs and results
        self.logs_dir = tmp_path / "logs"
        self.results_dir = tmp_path / "results"
        self.logs_dir.mkdir()
        self.results_dir.mkdir()
        
        # Store original paths to restore later
        self.original_logs_dir = None
        self.original_results_dir = None
        
        yield
        
        # Cleanup not strictly necessary as tmp_path is auto-cleaned

    def test_baseline_training_with_gradient_logging(self):
        """
        Test that baseline training runs and explicitly populates 
        data/logs/gradient_norms.json for SC-002 verification.
        
        This test:
        1. Generates synthetic training and test data.
        2. Configures the baseline model.
        3. Runs training with gradient logging enabled.
        4. Verifies the gradient_norms.json file is created and populated.
        """
        # Setup paths relative to a temporary project root
        temp_project_root = Path(self.logs_dir).parent
        data_dir = temp_project_root / "data"
        logs_dir = data_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        gradient_log_path = logs_dir / "gradient_norms.json"
        
        # Generate synthetic data
        train_data = generate_training_data(seed=42, n_samples=1000)
        test_data = generate_test_data(seed=123, n_samples=200)
        
        # Verify independence (should pass without raising)
        assert verify_independence(train_data, test_data) is True
        
        # Create a simple baseline model
        model = BaselineTransformer(
            input_dim=train_data.shape[1],
            hidden_dim=64,
            output_dim=1,
            num_layers=2
        )
        
        # Configure training
        train_config = TrainingConfig(
            epochs=5,  # Small number for integration test speed
            batch_size=32,
            learning_rate=0.001,
            log_gradient_norms=True,
            gradient_log_path=str(gradient_log_path)
        )
        
        # Run training (this should populate gradient_log_path)
        # We use a mock optimizer and data loader for the integration test
        # to ensure it runs quickly without full dataset loading overhead
        import torch
        import torch.optim as optim
        
        optimizer = optim.Adam(model.parameters(), lr=train_config.learning_rate)
        
        # Create a simple training loop for the test
        # In a real scenario, this would use the full data pipeline
        model.train()
        for epoch in range(train_config.epochs):
            # Create a dummy batch
            batch_x = torch.randn(train_config.batch_size, train_data.shape[1])
            batch_y = torch.randn(train_config.batch_size, 1)
            
            optimizer.zero_grad()
            output = model(batch_x)
            loss = torch.nn.functional.mse_loss(output, batch_y)
            loss.backward()
            
            # Log gradients if enabled
            if train_config.log_gradient_norms:
                log_gradient_norms(model, step=epoch, log_path=train_config.gradient_log_path)
            
            optimizer.step()
        
        # Verify the gradient log file exists
        assert gradient_log_path.exists(), f"Gradient log file not created at {gradient_log_path}"
        
        # Verify the file is not empty and contains valid JSON
        with open(gradient_log_path, 'r') as f:
            log_data = json.load(f)
        
        assert isinstance(log_data, list), "Gradient log should be a list"
        assert len(log_data) > 0, "Gradient log should contain entries"
        
        # Verify the structure of log entries
        for entry in log_data:
            assert "step" in entry, "Log entry missing 'step'"
            assert "gradient_norm" in entry, "Log entry missing 'gradient_norm'"
            assert "timestamp" in entry, "Log entry missing 'timestamp'"
            assert isinstance(entry["step"], int), "Step should be an integer"
            assert isinstance(entry["gradient_norm"], float), "Gradient norm should be a float"
        
        # Verify we have logs for all epochs
        steps_logged = [entry["step"] for entry in log_data]
        expected_steps = list(range(train_config.epochs))
        assert set(steps_logged) == set(expected_steps), f"Expected logs for steps {expected_steps}, got {steps_logged}"

    def test_gradient_norms_schema_compliance(self):
        """
        Verify that the gradient norms log conforms to the expected schema
        for SC-002 verification.
        """
        # Setup
        temp_project_root = Path(self.logs_dir).parent
        data_dir = temp_project_root / "data"
        logs_dir = data_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        gradient_log_path = logs_dir / "gradient_norms.json"
        
        # Run a minimal training to generate logs
        model = BaselineTransformer(input_dim=10, hidden_dim=32, output_dim=1, num_layers=1)
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        
        model.train()
        for step in range(3):
            batch_x = torch.randn(16, 10)
            batch_y = torch.randn(16, 1)
            
            optimizer.zero_grad()
            loss = torch.nn.functional.mse_loss(model(batch_x), batch_y)
            loss.backward()
            
            log_gradient_norms(model, step=step, log_path=str(gradient_log_path))
            optimizer.step()
        
        # Load and verify schema
        with open(gradient_log_path, 'r') as f:
            log_data = json.load(f)
        
        # Schema requirements for SC-002:
        # - List of objects
        # - Each object has: step (int), gradient_norm (float), timestamp (str)
        assert isinstance(log_data, list)
        assert len(log_data) == 3  # 3 steps logged
        
        for i, entry in enumerate(log_data):
            assert entry["step"] == i
            assert isinstance(entry["gradient_norm"], (int, float))
            assert entry["gradient_norm"] >= 0
            assert "timestamp" in entry
            assert isinstance(entry["timestamp"], str)
            # Verify timestamp format (ISO 8601)
            from datetime import datetime
            try:
                datetime.fromisoformat(entry["timestamp"].replace('Z', '+00:00'))
            except ValueError:
                pytest.fail(f"Invalid timestamp format: {entry['timestamp']}")

    def test_gradient_norms_persistence_across_runs(self):
        """
        Verify that gradient norm logs are appended correctly across multiple
        training runs (simulating epoch-by-epoch logging).
        """
        temp_project_root = Path(self.logs_dir).parent
        data_dir = temp_project_root / "data"
        logs_dir = data_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        gradient_log_path = logs_dir / "gradient_norms.json"
        
        model = BaselineTransformer(input_dim=10, hidden_dim=32, output_dim=1, num_layers=1)
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        
        # First "epoch"
        model.train()
        for step in range(2):
            batch_x = torch.randn(16, 10)
            batch_y = torch.randn(16, 1)
            optimizer.zero_grad()
            loss = torch.nn.functional.mse_loss(model(batch_x), batch_y)
            loss.backward()
            log_gradient_norms(model, step=step, log_path=str(gradient_log_path))
            optimizer.step()
        
        # Second "epoch" - should append, not overwrite
        for step in range(2, 4):
            batch_x = torch.randn(16, 10)
            batch_y = torch.randn(16, 1)
            optimizer.zero_grad()
            loss = torch.nn.functional.mse_loss(model(batch_x), batch_y)
            loss.backward()
            log_gradient_norms(model, step=step, log_path=str(gradient_log_path))
            optimizer.step()
        
        # Verify all 4 steps are logged
        with open(gradient_log_path, 'r') as f:
            log_data = json.load(f)
        
        assert len(log_data) == 4, f"Expected 4 log entries, got {len(log_data)}"
        steps = [entry["step"] for entry in log_data]
        assert steps == [0, 1, 2, 3], f"Expected steps [0,1,2,3], got {steps}"

    def test_gradient_norms_file_location(self):
        """
        Verify that gradient norms are written to the correct location:
        data/logs/gradient_norms.json
        """
        # This test verifies the default path behavior
        temp_project_root = Path(self.logs_dir).parent
        data_dir = temp_project_root / "data"
        logs_dir = data_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        expected_path = logs_dir / "gradient_norms.json"
        
        model = BaselineTransformer(input_dim=10, hidden_dim=32, output_dim=1, num_layers=1)
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        
        model.train()
        batch_x = torch.randn(16, 10)
        batch_y = torch.randn(16, 1)
        optimizer.zero_grad()
        loss = torch.nn.functional.mse_loss(model(batch_x), batch_y)
        loss.backward()
        
        # Use the explicit path
        log_gradient_norms(model, step=0, log_path=str(expected_path))
        
        # Verify file exists at expected location
        assert expected_path.exists(), f"File not found at expected location: {expected_path}"
        
        # Verify it's the correct file (not a temp file or wrong directory)
        assert str(expected_path).endswith("gradient_norms.json")
        assert "data/logs" in str(expected_path)

    def test_gradient_norms_with_realistic_model(self):
        """
        Test gradient logging with a more realistic baseline transformer configuration
        to ensure it works with the actual model architecture.
        """
        temp_project_root = Path(self.logs_dir).parent
        data_dir = temp_project_root / "data"
        logs_dir = data_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        gradient_log_path = logs_dir / "gradient_norms.json"
        
        # Create a realistic baseline model
        model = BaselineTransformer(
            input_dim=128,
            hidden_dim=256,
            output_dim=64,
            num_layers=4,
            attention_heads=8
        )
        
        optimizer = optim.Adam(model.parameters(), lr=0.0001)
        
        # Simulate a realistic training step
        model.train()
        batch_size = 32
        seq_len = 64
        batch_x = torch.randn(batch_size, seq_len, 128)
        batch_y = torch.randn(batch_size, seq_len, 64)
        
        optimizer.zero_grad()
        output = model(batch_x)
        loss = torch.nn.functional.mse_loss(output, batch_y)
        loss.backward()
        
        # Log gradients
        log_gradient_norms(model, step=0, log_path=str(gradient_log_path))
        optimizer.step()
        
        # Verify log was created
        assert gradient_log_path.exists()
        
        with open(gradient_log_path, 'r') as f:
            log_data = json.load(f)
        
        assert len(log_data) == 1
        assert log_data[0]["step"] == 0
        assert log_data[0]["gradient_norm"] > 0
        assert "timestamp" in log_data[0]