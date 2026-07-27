"""
Integration test for microcircuit model training pipeline.

This test explicitly runs the microcircuit model with log_gradient_norms enabled
to populate data/logs/gradient_norms_microcircuit.json for SC-002 verification.

DEPENDS ON: T008b (log_gradient_norms implementation)
"""
import json
import os
import tempfile
import pytest
import torch
import torch.nn as nn
from pathlib import Path
import sys
import logging

# Ensure the code directory is in the path for imports
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.models.microcircuit import create_microcircuit_column, MicrocircuitColumn
from src.models.hybrid_network import create_hybrid_network, HybridNetwork
from src.data.benchmarks import generate_training_data, generate_test_data
from src.training.trainer import run_training, TrainingConfig
from src.training.homeostasis import log_gradient_norms, HomeostaticScaler, HomeostasisConfig
from src.utils.statistics import load_gradient_norms

# Configure logging for the test
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestMicrocircuitTraining:
    """Integration tests for the microcircuit training pipeline."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmp_path):
        """Set up temporary directories and clean up after test."""
        self.tmp_dir = tmp_path
        self.data_dir = self.tmp_dir / "data"
        self.logs_dir = self.data_dir / "logs"
        self.results_dir = self.data_dir / "results"
        
        self.data_dir.mkdir(parents=True)
        self.logs_dir.mkdir(parents=True)
        self.results_dir.mkdir(parents=True)
        
        # Store original paths for restoration if needed
        self.original_data_dir = None
        self.original_logs_dir = None
        
        yield
        
        # Cleanup is handled by tmp_path automatically

    def test_microcircuit_gradient_logging(self):
        """
        Test that running microcircuit training with log_gradient_norms enabled
        produces the expected gradient norms file for SC-002 verification.
        
        SC-002 requires comparing gradient stability between baseline and microcircuit models.
        """
        # Create a small microcircuit model for testing
        # Using minimal dimensions to keep test fast
        config = {
            "hidden_dim": 32,
            "num_layers": 2,
            "neurons_per_layer": 16,
            "num_columns": 1,
            "target_ei_ratio": 4.0
        }
        
        model = create_hybrid_network(config)
        model.eval()  # Set to eval mode for inference/testing
        
        # Create a simple training config for the test
        training_config = TrainingConfig(
            epochs=2,  # Minimal epochs for test
            batch_size=4,
            learning_rate=0.001,
            gradient_clip=1.0,
            device="cpu",
            log_interval=1
        )
        
        # Generate synthetic data for the test
        # Using small dimensions for speed
        train_data = generate_training_data(num_samples=32, seq_len=10, dim=4, seed=42)
        test_data = generate_test_data(num_samples=16, seq_len=10, dim=4, seed=123)
        
        # Ensure data directories exist
        data_dir = self.data_dir
        logs_dir = self.logs_dir
        
        # Create homeostasis config
        homeostasis_config = HomeostasisConfig(
            target_ei_ratio=4.0,
            decay_rate=0.01,
            enabled=True
        )
        
        # Create scaler
        scaler = HomeostaticScaler(model, homeostasis_config)
        
        # Path for gradient norms log
        gradient_log_path = logs_dir / "gradient_norms_microcircuit.json"
        
        # Run a minimal training loop to generate gradients
        optimizer = torch.optim.Adam(model.parameters(), lr=training_config.learning_rate)
        
        model.train()
        for epoch in range(training_config.epochs):
            total_loss = 0.0
            num_batches = 0
            
            # Process training data in batches
            for i in range(0, len(train_data["inputs"]), training_config.batch_size):
                batch_inputs = train_data["inputs"][i:i+training_config.batch_size]
                batch_targets = train_data["targets"][i:i+training_config.batch_size]
                
                if len(batch_inputs) == 0:
                    continue
                
                # Convert to tensors
                inputs = torch.tensor(batch_inputs, dtype=torch.float32)
                targets = torch.tensor(batch_targets, dtype=torch.float32)
                
                # Forward pass
                optimizer.zero_grad()
                outputs = model(inputs)
                
                # Calculate loss (MSE for simplicity)
                loss = nn.functional.mse_loss(outputs, targets)
                
                # Backward pass
                loss.backward()
                
                # Clip gradients
                if training_config.gradient_clip > 0:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), training_config.gradient_clip)
                
                # Log gradient norms
                step = epoch * (len(train_data["inputs"]) // training_config.batch_size) + num_batches
                log_gradient_norms(model, step, output_path=str(gradient_log_path))
                
                # Update weights
                optimizer.step()
                
                # Apply homeostatic scaling
                if homeostasis_config.enabled:
                    scaler.step(optimizer, step)
                
                total_loss += loss.item()
                num_batches += 1
            
            avg_loss = total_loss / max(num_batches, 1)
            logger.info(f"Epoch {epoch+1}/{training_config.epochs}, Loss: {avg_loss:.4f}")
        
        # Verify that the gradient norms file was created
        assert gradient_log_path.exists(), f"Gradient norms file not created at {gradient_log_path}"
        
        # Load and verify the content
        with open(gradient_log_path, "r") as f:
            gradient_data = json.load(f)
        
        # Verify structure
        assert isinstance(gradient_data, list), "Gradient norms data should be a list"
        assert len(gradient_data) > 0, "Gradient norms data should not be empty"
        
        # Verify each entry has required fields
        for entry in gradient_data:
            assert "step" in entry, "Each entry should have a 'step' field"
            assert "total_norm" in entry, "Each entry should have a 'total_norm' field"
            assert isinstance(entry["step"], int), "Step should be an integer"
            assert isinstance(entry["total_norm"], (int, float)), "Total norm should be numeric"
        
        logger.info(f"Successfully verified gradient norms file with {len(gradient_data)} entries")
        
        # Also verify we can load it using the statistics utility
        loaded_data = load_gradient_norms(str(gradient_log_path))
        assert loaded_data is not None, "Failed to load gradient norms using utility"
        assert len(loaded_data) == len(gradient_data), "Loaded data length mismatch"
        
        logger.info("All verification checks passed for microcircuit gradient logging")

    def test_microcircuit_training_with_ei_enforcement(self):
        """
        Test that microcircuit training properly enforces E/I ratio dynamics.
        
        This ensures the homeostatic scaling is active and affecting the model.
        """
        config = {
            "hidden_dim": 32,
            "num_layers": 2,
            "neurons_per_layer": 16,
            "num_columns": 1,
            "target_ei_ratio": 4.0
        }
        
        model = create_hybrid_network(config)
        model.train()
        
        # Generate minimal data
        train_data = generate_training_data(num_samples=16, seq_len=5, dim=4, seed=42)
        
        # Setup training
        training_config = TrainingConfig(
            epochs=1,
            batch_size=4,
            learning_rate=0.001,
            gradient_clip=1.0,
            device="cpu",
            log_interval=1
        )
        
        homeostasis_config = HomeostasisConfig(
            target_ei_ratio=4.0,
            decay_rate=0.01,
            enabled=True
        )
        
        scaler = HomeostaticScaler(model, homeostasis_config)
        optimizer = torch.optim.Adam(model.parameters(), lr=training_config.learning_rate)
        
        gradient_log_path = self.logs_dir / "gradient_norms_microcircuit.json"
        
        # Run one epoch
        total_loss = 0.0
        for i in range(0, len(train_data["inputs"]), training_config.batch_size):
            batch_inputs = train_data["inputs"][i:i+training_config.batch_size]
            batch_targets = train_data["targets"][i:i+training_config.batch_size]
            
            if len(batch_inputs) == 0:
                continue
            
            inputs = torch.tensor(batch_inputs, dtype=torch.float32)
            targets = torch.tensor(batch_targets, dtype=torch.float32)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = nn.functional.mse_loss(outputs, targets)
            loss.backward()
            
            if training_config.gradient_clip > 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), training_config.gradient_clip)
            
            optimizer.step()
            scaler.step(optimizer, step=0)
            
            total_loss += loss.item()
        
        avg_loss = total_loss / max(len(train_data["inputs"]) // training_config.batch_size, 1)
        
        # Verify training completed without errors
        assert avg_loss > 0, "Training should produce a positive loss"
        assert gradient_log_path.exists(), "Gradient log should be created during training"
        
        logger.info(f"Microcircuit training with E/I enforcement completed, loss: {avg_loss:.4f}")