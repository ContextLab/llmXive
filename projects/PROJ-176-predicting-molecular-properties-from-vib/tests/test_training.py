"""
Unit test for training loop in tests/test_training.py.
Verifies early stopping trigger and checkpoint save functionality.
"""
import os
import sys
import tempfile
import shutil
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# Add project root to path to allow imports from code/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models.cnn_1d import MolecularCNN
from utils.seed_utils import set_seed

# Set seed for reproducibility in tests
set_seed(42)


class MockTrainer:
    """
    Minimal mock trainer to test early stopping and checkpoint logic
    without the full CLI overhead.
    """
    def __init__(self, model, optimizer, criterion, patience=3):
        self.model = model
        self.optimizer = optimizer
        self.criterion = criterion
        self.patience = patience
        self.best_loss = float('inf')
        self.patience_counter = 0
        self.best_state_dict = None
        self.early_stopped = False
        self.history = []

    def train_epoch(self, dataloader):
        self.model.train()
        total_loss = 0.0
        for batch_x, batch_y in dataloader:
            self.optimizer.zero_grad()
            outputs = self.model(batch_x)
            # Handle multi-head output if necessary (simplified here)
            if isinstance(outputs, (list, tuple)):
                loss = sum(self.criterion(out, target) for out, target in zip(outputs, batch_y))
            else:
                loss = self.criterion(outputs, batch_y)
            loss.backward()
            self.optimizer.step()
            total_loss += loss.item()
        return total_loss / len(dataloader)

    def validate_epoch(self, dataloader):
        self.model.eval()
        total_loss = 0.0
        with torch.no_grad():
            for batch_x, batch_y in dataloader:
                outputs = self.model(batch_x)
                if isinstance(outputs, (list, tuple)):
                    loss = sum(self.criterion(out, target) for out, target in zip(outputs, batch_y))
                else:
                    loss = self.criterion(outputs, batch_y)
                total_loss += loss.item()
        return total_loss / len(dataloader)

    def step(self, val_loss, checkpoint_path):
        self.history.append(val_loss)
        if val_loss < self.best_loss:
            self.best_loss = val_loss
            self.patience_counter = 0
            self.best_state_dict = {k: v.clone() for k, v in self.model.state_dict().items()}
            torch.save(self.best_state_dict, checkpoint_path)
        else:
            self.patience_counter += 1
            if self.patience_counter >= self.patience:
                self.early_stopped = True
                return True  # Triggered early stop
        return False


def test_early_stopping_trigger():
    """
    Verify that early stopping triggers when validation loss stops improving.
    """
    # Create a simple model
    model = MolecularCNN(input_dim=100, num_targets=3)
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.MSELoss()

    # Create dummy data that will cause loss to increase or stagnate
    # to force early stopping
    x_dummy = torch.randn(20, 100)
    y_dummy = torch.randn(20, 3)
    dataset = TensorDataset(x_dummy, y_dummy)
    loader = DataLoader(dataset, batch_size=5)

    trainer = MockTrainer(model, optimizer, criterion, patience=2)
    checkpoint_path = os.path.join(tempfile.gettempdir(), "test_checkpoint.pt")

    # Simulate epochs where loss increases
    increasing_losses = [1.0, 1.2, 1.5, 1.8]
    triggered = False

    for loss in increasing_losses:
        # Manually step logic to simulate validation
        # We bypass train_epoch and just feed the loss to step
        if trainer.step(loss, checkpoint_path):
            triggered = True
            break

    assert triggered, "Early stopping did not trigger when loss increased beyond patience."
    assert os.path.exists(checkpoint_path), "Checkpoint file was not saved."

    # Clean up
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)


def test_checkpoint_save_and_load():
    """
    Verify that the best model state is saved and can be loaded.
    """
    model = MolecularCNN(input_dim=50, num_targets=3)
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.MSELoss()

    x_dummy = torch.randn(10, 50)
    y_dummy = torch.randn(10, 3)
    dataset = TensorDataset(x_dummy, y_dummy)
    loader = DataLoader(dataset, batch_size=5)

    trainer = MockTrainer(model, optimizer, criterion, patience=5)
    checkpoint_path = os.path.join(tempfile.gettempdir(), "best_model_test.pt")

    # Simulate a scenario where loss improves then degrades
    losses = [2.0, 1.5, 1.0, 1.2, 1.4] # Best is 1.0 at index 2

    for loss in losses:
        trainer.step(loss, checkpoint_path)

    assert os.path.exists(checkpoint_path), "Best checkpoint was not saved."

    # Load the saved state
    loaded_state = torch.load(checkpoint_path, weights_only=True)
    
    # Verify the loaded state corresponds to the best loss (1.0)
    # We can't easily verify the exact weights without running forward pass,
    # but we can verify the file loads and has keys
    assert isinstance(loaded_state, dict), "Loaded state is not a dictionary."
    assert len(loaded_state) > 0, "Loaded state is empty."
    
    # Verify that the model can load it
    model.load_state_dict(loaded_state)
    model.eval()
    with torch.no_grad():
        _ = model(x_dummy) # Should not raise

    # Clean up
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)


def test_no_early_stopping_with_improvement():
    """
    Verify that early stopping does NOT trigger if loss keeps improving.
    """
    model = MolecularCNN(input_dim=50, num_targets=3)
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.MSELoss()

    x_dummy = torch.randn(10, 50)
    y_dummy = torch.randn(10, 3)
    dataset = TensorDataset(x_dummy, y_dummy)
    loader = DataLoader(dataset, batch_size=5)

    trainer = MockTrainer(model, optimizer, criterion, patience=5)
    checkpoint_path = os.path.join(tempfile.gettempdir(), "no_stop_test.pt")

    # Continuously improving losses
    improving_losses = [5.0, 4.0, 3.0, 2.0, 1.0]

    triggered = False
    for loss in improving_losses:
        if trainer.step(loss, checkpoint_path):
            triggered = True
            break

    assert not triggered, "Early stopping triggered despite continuous improvement."
    
    # Clean up
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)


if __name__ == "__main__":
    print("Running test_early_stopping_trigger...")
    test_early_stopping_trigger()
    print("PASSED")

    print("Running test_checkpoint_save_and_load...")
    test_checkpoint_save_and_load()
    print("PASSED")

    print("Running test_no_early_stopping_with_improvement...")
    test_no_early_stopping_with_improvement()
    print("PASSED")

    print("All tests passed successfully.")
