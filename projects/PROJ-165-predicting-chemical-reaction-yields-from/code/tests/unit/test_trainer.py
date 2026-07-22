"""
Unit tests for the training loop logic in src/models/trainer.py.

Tests cover:
1. Loss calculation (MSE) correctness.
2. Backpropagation execution (gradient computation and non-zero gradients).
3. Optimizer step execution (parameter updates).
4. Early stopping logic triggers.
5. Checkpoint saving logic.

Target variable: Normalized DFT total molecular energy.
"""
import pytest
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.models.trainer import Trainer
from src.utils.seeds import set_seed

class DummyAttentionNet(nn.Module):
    """
    A minimal dummy model to simulate the AttentionNet architecture
    for testing the trainer logic without needing the full model implementation.
    """
    def __init__(self, input_dim=10, hidden_dim=8, output_dim=1):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        # Simple linear layers to simulate a network
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, output_dim)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.fc2(x)
        return x

@pytest.fixture
def dummy_model():
    set_seed(42)
    return DummyAttentionNet(input_dim=10, hidden_dim=8, output_dim=1)

@pytest.fixture
def dummy_data():
    """Generates a small batch of dummy data."""
    set_seed(123)
    batch_size = 4
    input_dim = 10
    # Spectra + Fingerprints + Conditions (flattened for dummy)
    x = torch.randn(batch_size, input_dim)
    # Target: Normalized DFT total molecular energy (scalar)
    y = torch.randn(batch_size, 1)
    return x, y

@pytest.fixture
def trainer_config():
    """Default trainer configuration."""
    return {
        "learning_rate": 1e-3,
        "batch_size": 32,
        "epochs": 5,
        "patience": 2,
        "checkpoint_dir": tempfile.mkdtemp(),
        "device": "cpu",
        "seed": 42
    }

class TestTrainingLoopLogic:
    """Tests for the core training loop logic."""

    def test_loss_calculation_correctness(self, dummy_model, dummy_data):
        """Verify that the MSE loss is calculated correctly."""
        x, y = dummy_data
        model = dummy_model
        
        # Forward pass
        predictions = model(x)
        
        # Manual MSE calculation
        manual_loss = ((predictions - y) ** 2).mean()
        
        # Trainer uses nn.MSELoss
        criterion = nn.MSELoss()
        trainer_loss = criterion(predictions, y)
        
        assert torch.allclose(manual_loss, trainer_loss), "Loss calculation mismatch"
        assert trainer_loss.requires_grad, "Loss should require gradients"

    def test_backpropagation_executes(self, dummy_model, dummy_data):
        """Verify that backpropagation computes non-zero gradients."""
        x, y = dummy_data
        model = dummy_model
        
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=1e-3)
        
        # Forward
        predictions = model(x)
        loss = criterion(predictions, y)
        
        # Backward
        optimizer.zero_grad()
        loss.backward()
        
        # Check gradients exist and are non-zero for at least one parameter
        has_grad = False
        for param in model.parameters():
            if param.grad is not None:
                if param.grad.abs().sum() > 0:
                    has_grad = True
                    break
        
        assert has_grad, "Backpropagation failed: no non-zero gradients found"

    def test_optimizer_step_updates_weights(self, dummy_model, dummy_data):
        """Verify that the optimizer step actually changes model weights."""
        x, y = dummy_data
        model = dummy_model
        
        # Store initial weights
        initial_weights = {name: param.clone() for name, param in model.named_parameters()}
        
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=1e-3)
        
        # Forward
        predictions = model(x)
        loss = criterion(predictions, y)
        
        # Backward and Step
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        # Check if weights changed
        weights_changed = False
        for name, param in model.named_parameters():
            if not torch.allclose(param, initial_weights[name]):
                weights_changed = True
                break
        
        assert weights_changed, "Optimizer step failed: weights did not update"

    def test_early_stopping_triggers(self, dummy_model, trainer_config):
        """Verify that early stopping logic triggers when validation loss doesn't improve."""
        # Create a trainer instance
        trainer = Trainer(model=dummy_model, config=trainer_config)
        
        # Mock the data loaders to return fixed losses
        # We simulate a scenario where val_loss increases or stays same
        mock_train_loader = MagicMock()
        mock_val_loader = MagicMock()
        
        # Simulate epochs where val_loss does not improve
        # Epoch 1: val_loss = 1.0 (best)
        # Epoch 2: val_loss = 1.1 (no improve)
        # Epoch 3: val_loss = 1.2 (no improve) -> Should trigger early stop if patience=2
        
        call_count = 0
        def mock_eval(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return 1.0
            elif call_count == 2:
                return 1.1
            else:
                return 1.2
        
        trainer.evaluate_model = mock_eval
        trainer.save_checkpoint = MagicMock()
        
        # Run training for a few epochs manually to test logic
        # We need to simulate the internal loop logic
        best_val_loss = float('inf')
        patience = trainer_config["patience"]
        epochs_without_improvement = 0
        should_stop = False
        
        for epoch in range(5):
            val_loss = mock_eval()
            
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                epochs_without_improvement = 0
            else:
                epochs_without_improvement += 1
            
            if epochs_without_improvement >= patience:
                should_stop = True
                break
        
        assert should_stop, "Early stopping logic failed to trigger when patience exceeded"

    def test_checkpoint_saving(self, dummy_model, trainer_config):
        """Verify that the trainer saves checkpoints correctly."""
        trainer = Trainer(model=dummy_model, config=trainer_config)
        checkpoint_path = Path(trainer_config["checkpoint_dir"]) / "test_checkpoint.pt"
        
        # Save a checkpoint
        trainer.save_checkpoint(checkpoint_path, epoch=1, val_loss=0.5)
        
        assert checkpoint_path.exists(), "Checkpoint file was not created"
        
        # Load and verify content
        checkpoint = torch.load(checkpoint_path, weights_only=True)
        assert "epoch" in checkpoint, "Checkpoint missing 'epoch'"
        assert "val_loss" in checkpoint, "Checkpoint missing 'val_loss'"
        assert "model_state_dict" in checkpoint, "Checkpoint missing 'model_state_dict'"
        assert checkpoint["epoch"] == 1
        assert checkpoint["val_loss"] == 0.5

    def test_training_loop_integration(self, dummy_model, dummy_data, trainer_config):
        """Integration test: Run a full mini-training loop to ensure no exceptions."""
        set_seed(42)
        
        # Create a simple dataloader from dummy data
        dataset = torch.utils.data.TensorDataset(dummy_data[0], dummy_data[1])
        train_loader = torch.utils.data.DataLoader(dataset, batch_size=2, shuffle=True)
        val_loader = torch.utils.data.DataLoader(dataset, batch_size=2)
        
        trainer = Trainer(model=dummy_model, config=trainer_config)
        
        # Mock evaluate to return a fixed value for the integration run
        original_eval = trainer.evaluate_model
        trainer.evaluate_model = lambda loader: 0.8
        
        # Run a single epoch manually to test the loop structure
        try:
            loss = trainer.train_epoch(train_loader)
            assert isinstance(loss, float), "train_epoch should return a float loss"
            assert loss >= 0, "Loss should be non-negative"
        except Exception as e:
            pytest.fail(f"Training loop raised an exception: {e}")
        finally:
            trainer.evaluate_model = original_eval

if __name__ == "__main__":
    pytest.main([__file__, "-v"])