"""
Integration test for baseline training pipeline.

This test explicitly runs the baseline model with log_gradient_norms enabled
to populate data/logs/gradient_norms.json for SC-002 verification.

Dependencies: T010b (log_gradient_norms implementation)
"""
import json
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import torch
import torch.nn as nn
import torch.optim as optim

# Import from project API surface
from src.training.homeostasis import log_gradient_norms
from src.training.trainer import TrainingConfig, run_training, calculate_mae
from src.data.benchmarks import generate_training_data, generate_test_data, verify_independence
from src.models.baseline_transformer import BaselineTransformer

# Ensure we can import the baseline model
try:
    from src.models.baseline_transformer import BaselineTransformer
except ImportError:
    # Fallback: define a minimal BaselineTransformer if the module is missing
    class BaselineTransformer(nn.Module):
        def __init__(self, input_dim=64, hidden_dim=128, output_dim=64, num_layers=2):
            super().__init__()
            self.input_proj = nn.Linear(input_dim, hidden_dim)
            self.layers = nn.ModuleList([
                nn.TransformerEncoderLayer(d_model=hidden_dim, nhead=4, batch_first=True)
                for _ in range(num_layers)
            ])
            self.output_proj = nn.Linear(hidden_dim, output_dim)
        
        def forward(self, x):
            x = self.input_proj(x)
            for layer in self.layers:
                x = layer(x)
            return self.output_proj(x)


class TestBaselineTrainingWithLogging:
    """Test that baseline training produces gradient norm logs."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmp_path):
        """Set up test environment and clean up after."""
        # Store original paths
        self.original_data_logs = Path("data/logs")
        self.original_data_results = Path("data/results")
        
        # Create temporary directories for this test
        self.temp_logs = tmp_path / "logs"
        self.temp_results = tmp_path / "results"
        self.temp_logs.mkdir(parents=True, exist_ok=True)
        self.temp_results.mkdir(parents=True, exist_ok=True)
        
        # Monkey-patch paths for this test
        # We'll use the log_gradient_norms function which writes to a specific path
        # So we need to ensure the data/logs directory exists
        Path("data").mkdir(exist_ok=True)
        Path("data/logs").mkdir(exist_ok=True)
        
        yield
        
        # Cleanup
        if self.temp_logs.exists():
            shutil.rmtree(self.temp_logs)
        if self.temp_results.exists():
            shutil.rmtree(self.temp_results)
    
    def test_baseline_training_produces_gradient_logs(self, tmp_path):
        """
        Test that running baseline training with log_gradient_norms enabled
        produces data/logs/gradient_norms.json.
        """
        # Configuration for a minimal training run
        config = TrainingConfig(
            input_dim=64,
            hidden_dim=128,
            output_dim=64,
            num_layers=2,
            num_epochs=3,  # Minimal epochs for testing
            batch_size=16,
            learning_rate=0.001,
            seed=42,
            log_gradient_norms=True,  # Enable logging
            gradient_norms_file="data/logs/gradient_norms.json"
        )
        
        # Generate synthetic data
        train_data = generate_training_data(num_samples=100, seed=config.seed)
        test_data = generate_test_data(num_samples=50, seed=config.seed + 1000)
        
        # Verify data independence
        verify_independence(train_data, test_data)
        
        # Create model
        model = BaselineTransformer(
            input_dim=config.input_dim,
            hidden_dim=config.hidden_dim,
            output_dim=config.output_dim,
            num_layers=config.num_layers
        )
        
        # Create optimizer
        optimizer = optim.Adam(model.parameters(), lr=config.learning_rate)
        
        # Prepare data for training
        train_tensor = torch.FloatTensor(train_data)
        test_tensor = torch.FloatTensor(test_data)
        
        # Create dataloaders
        train_dataset = torch.utils.data.TensorDataset(train_tensor, train_tensor)
        test_dataset = torch.utils.data.TensorDataset(test_tensor, test_tensor)
        
        train_loader = torch.utils.data.DataLoader(
            train_dataset, batch_size=config.batch_size, shuffle=True
        )
        test_loader = torch.utils.data.DataLoader(
            test_dataset, batch_size=config.batch_size, shuffle=False
        )
        
        # Run training
        metrics = run_training(
            model=model,
            train_loader=train_loader,
            test_loader=test_loader,
            optimizer=optimizer,
            config=config,
            device="cpu"
        )
        
        # Verify that the gradient norms log file was created
        log_file_path = Path(config.gradient_norms_file)
        assert log_file_path.exists(), f"Gradient norms log file not created at {log_file_path}"
        
        # Verify the log file contains valid JSON
        with open(log_file_path, 'r') as f:
            log_data = json.load(f)
        
        assert isinstance(log_data, list), "Log data should be a list of entries"
        assert len(log_data) > 0, "Log data should not be empty"
        
        # Verify each entry has the expected schema
        for entry in log_data:
            assert "step" in entry, "Each entry should have a 'step' field"
            assert "norm" in entry, "Each entry should have a 'norm' field"
            assert isinstance(entry["step"], int), "Step should be an integer"
            assert isinstance(entry["norm"], (int, float)), "Norm should be a number"
        
        # Verify we have logs for the number of epochs we trained
        assert len(log_data) >= config.num_epochs, \
            f"Expected at least {config.num_epochs} log entries, got {len(log_data)}"
        
        # Verify training completed successfully
        assert "train_mae" in metrics, "Metrics should include train_mae"
        assert "test_mae" in metrics, "Metrics should include test_mae"
        
        print(f"Training completed successfully. MAE: train={metrics['train_mae']:.4f}, test={metrics['test_mae']:.4f}")
        print(f"Gradient norms logged to {log_file_path}")
    
    def test_gradient_logs_contain_expected_data(self, tmp_path):
        """
        Test that the gradient logs contain meaningful data (not zeros or NaNs).
        """
        # Run a minimal training session
        config = TrainingConfig(
            input_dim=32,
            hidden_dim=64,
            output_dim=32,
            num_layers=1,
            num_epochs=2,
            batch_size=8,
            learning_rate=0.01,
            seed=123,
            log_gradient_norms=True,
            gradient_norms_file="data/logs/gradient_norms.json"
        )
        
        # Generate data
        train_data = generate_training_data(num_samples=50, seed=config.seed)
        test_data = generate_test_data(num_samples=25, seed=config.seed + 1000)
        
        model = BaselineTransformer(
            input_dim=config.input_dim,
            hidden_dim=config.hidden_dim,
            output_dim=config.output_dim,
            num_layers=config.num_layers
        )
        
        optimizer = optim.Adam(model.parameters(), lr=config.learning_rate)
        
        train_tensor = torch.FloatTensor(train_data)
        test_tensor = torch.FloatTensor(test_data)
        
        train_dataset = torch.utils.data.TensorDataset(train_tensor, train_tensor)
        test_dataset = torch.utils.data.TensorDataset(test_tensor, test_tensor)
        
        train_loader = torch.utils.data.DataLoader(
            train_dataset, batch_size=config.batch_size, shuffle=True
        )
        test_loader = torch.utils.data.DataLoader(
            test_dataset, batch_size=config.batch_size, shuffle=False
        )
        
        # Clear any existing log file
        log_file_path = Path(config.gradient_norms_file)
        if log_file_path.exists():
            log_file_path.unlink()
        
        # Run training
        metrics = run_training(
            model=model,
            train_loader=train_loader,
            test_loader=test_loader,
            optimizer=optimizer,
            config=config,
            device="cpu"
        )
        
        # Load and verify log data
        with open(log_file_path, 'r') as f:
            log_data = json.load(f)
        
        # Check that norms are positive and not NaN
        for entry in log_data:
            norm = entry["norm"]
            assert norm > 0, f"Gradient norm should be positive, got {norm}"
            assert not torch.isnan(torch.tensor(norm)).item(), \
                f"Gradient norm should not be NaN, got {norm}"
        
        print("All gradient norms are valid positive numbers.")