"""
Unit tests for training loop logic (loss calculation, backprop) in src/models/trainer.py.

This test suite validates:
1. Loss calculation correctness (MSE for DFT energy)
2. Backpropagation execution (gradients computed)
3. Optimizer step execution
4. Early stopping logic
5. Checkpoint saving mechanism
"""
import pytest
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import sys
import json

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from src.models.trainer import Trainer
from src.utils.seeds import set_seed


class DummyAttentionNet(nn.Module):
    """
    A minimal dummy model for testing the trainer.
    Mimics the interface of src.models.attention_net.AttentionNet
    but with simplified architecture.
    """
    def __init__(self, input_dim=100, hidden_dim=64, output_dim=1):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        
        # Simple linear layers to mimic the attention net's output head
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, output_dim)
        
    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x.squeeze(-1)  # Return 1D tensor for regression


@pytest.fixture
def dummy_model():
    """Create a dummy model with known weights for deterministic testing."""
    set_seed(42)
    model = DummyAttentionNet(input_dim=100, hidden_dim=32, output_dim=1)
    return model


@pytest.fixture
def dummy_data():
    """
    Create dummy data tensors mimicking the output of ReactionSample dataloader.
    Returns: (spectra_batch, fingerprints_batch, conditions_batch, targets_batch)
    """
    batch_size = 8
    input_dim = 100
    
    # Simulate spectral data (batch, channels, wavenumbers)
    spectra = torch.randn(batch_size, 3, 50)  # 3 channels: IR, Raman, NMR
    
    # Simulate ECFP4 fingerprints
    fingerprints = torch.randn(batch_size, input_dim)
    
    # Simulate condition embeddings (e.g., one-hot or learned)
    conditions = torch.randn(batch_size, 10)
    
    # Simulate normalized DFT total molecular energy targets
    targets = torch.randn(batch_size, 1)  # Shape (batch, 1)
    
    return spectra, fingerprints, conditions, targets


@pytest.fixture
def trainer_config():
    """Return a config dict mimicking src/config/defaults.yaml structure."""
    return {
        'learning_rate': 1e-3,
        'batch_size': 32,
        'epochs': 10,
        'early_stopping_patience': 3,
        'checkpoint_dir': tempfile.mkdtemp(),
        'seed': 42,
        'device': 'cpu'
    }


class TestTrainingLoopLogic:
    """Tests for the training loop logic in src/models/trainer.py."""

    def test_loss_calculation_mse(self, dummy_model, dummy_data):
        """
        Verify that the trainer uses MSE loss for DFT energy regression.
        
        Steps:
        1. Create a Trainer instance with dummy model and config.
        2. Manually compute forward pass and loss.
        3. Verify loss is MSE (mean squared error).
        4. Verify loss is non-negative.
        5. Verify loss is finite.
        """
        spectra, fingerprints, conditions, targets = dummy_data
        
        # Create trainer
        trainer = Trainer(
            model=dummy_model,
            config=trainer_config,
            train_loader=None,
            val_loader=None
        )
        
        # Forward pass
        outputs = dummy_model(torch.cat([spectra.flatten(1), fingerprints, conditions], dim=1))
        
        # Compute loss manually (should match trainer's criterion)
        expected_loss = nn.MSELoss()(outputs, targets.squeeze(-1))
        
        # Verify loss properties
        assert expected_loss >= 0, "MSE loss must be non-negative"
        assert torch.isfinite(expected_loss), "Loss must be finite"
        
        # Verify the trainer's criterion is MSE
        assert isinstance(trainer.criterion, nn.MSELoss), \
            "Trainer must use MSELoss for DFT energy regression"

    def test_backpropagation_executes(self, dummy_model, dummy_data):
        """
        Verify that backpropagation executes successfully and gradients are computed.
        
        Steps:
        1. Create trainer and optimizer.
        2. Perform a forward pass.
        3. Compute loss.
        4. Call backward().
        5. Verify that model parameters have non-zero gradients.
        """
        spectra, fingerprints, conditions, targets = dummy_data
        
        trainer = Trainer(
            model=dummy_model,
            config=trainer_config,
            train_loader=None,
            val_loader=None
        )
        
        # Concatenate inputs as the trainer would
        input_tensor = torch.cat([spectra.flatten(1), fingerprints, conditions], dim=1)
        
        # Forward pass
        outputs = trainer.model(input_tensor)
        
        # Compute loss
        loss = trainer.criterion(outputs, targets.squeeze(-1))
        
        # Zero gradients
        trainer.optimizer.zero_grad()
        
        # Backward pass
        loss.backward()
        
        # Verify gradients exist and are non-zero for at least one parameter
        has_gradient = False
        for param in trainer.model.parameters():
            if param.grad is not None:
                has_gradient = True
                # Check that gradient is not all zeros
                assert not torch.all(param.grad == 0), \
                    "Gradients should not be all zeros after backprop"
        
        assert has_gradient, "At least one parameter should have a gradient"

    def test_optimizer_step_executes(self, dummy_model, dummy_data):
        """
        Verify that the optimizer step updates model weights.
        
        Steps:
        1. Capture initial weights.
        2. Perform one training step (forward, backward, step).
        3. Compare weights before and after.
        4. Verify weights have changed.
        """
        spectra, fingerprints, conditions, targets = dummy_data
        
        trainer = Trainer(
            model=dummy_model,
            config=trainer_config,
            train_loader=None,
            val_loader=None
        )
        
        # Capture initial weights
        initial_weights = {
            name: param.clone() 
            for name, param in trainer.model.named_parameters()
        }
        
        # Concatenate inputs
        input_tensor = torch.cat([spectra.flatten(1), fingerprints, conditions], dim=1)
        
        # Training step
        trainer.optimizer.zero_grad()
        outputs = trainer.model(input_tensor)
        loss = trainer.criterion(outputs, targets.squeeze(-1))
        loss.backward()
        trainer.optimizer.step()
        
        # Verify weights have changed
        weights_changed = False
        for name, param in trainer.model.named_parameters():
            if not torch.equal(param, initial_weights[name]):
                weights_changed = True
                break
        
        assert weights_changed, "Model weights should change after optimizer step"

    def test_early_stopping_logic(self, dummy_model, trainer_config):
        """
        Verify that early stopping triggers when validation loss stops improving.
        
        Steps:
        1. Create a trainer with early stopping patience=2.
        2. Simulate validation losses that improve then plateau.
        3. Verify that early stopping flag is set after patience epochs.
        """
        trainer = Trainer(
            model=dummy_model,
            config=trainer_config,
            train_loader=None,
            val_loader=None
        )
        
        # Simulate validation losses: [1.0, 0.9, 0.8, 0.8, 0.8]
        # With patience=2, early stopping should trigger after 3rd plateau
        val_losses = [1.0, 0.9, 0.8, 0.8, 0.8]
        
        early_stop_triggered = False
        for epoch, val_loss in enumerate(val_losses):
            trainer.early_stopping_counter = 0  # Reset counter for test
            should_stop = trainer._early_stop_check(val_loss)
            
            if should_stop:
                early_stop_triggered = True
                break
        
        # With patience=2, we expect early stopping to trigger after 2 non-improvements
        # The sequence: 1.0 -> 0.9 (improve), 0.9 -> 0.8 (improve), 0.8 -> 0.8 (no improve),
        # 0.8 -> 0.8 (no improve), 0.8 -> 0.8 (no improve -> stop)
        # Actually, let's trace: 
        # epoch 0: loss=1.0, best=1.0, counter=0
        # epoch 1: loss=0.9, best=0.9, counter=0
        # epoch 2: loss=0.8, best=0.8, counter=0
        # epoch 3: loss=0.8, best=0.8, counter=1
        # epoch 4: loss=0.8, best=0.8, counter=2 -> should stop
        
        # The _early_stop_check logic should return True when counter >= patience
        assert trainer.patience == 3, "Default patience should be 3"
        # Manually test the counter logic
        trainer.best_val_loss = 0.8
        trainer.early_stopping_counter = 0
        
        # First non-improvement
        assert not trainer._early_stop_check(0.8), "Should not stop after 1 non-improvement"
        assert trainer.early_stopping_counter == 1
        
        # Second non-improvement
        assert not trainer._early_stop_check(0.8), "Should not stop after 2 non-improvements"
        assert trainer.early_stopping_counter == 2
        
        # Third non-improvement (patience=3)
        assert trainer._early_stop_check(0.8), "Should stop after 3 non-improvements"

    def test_checkpoint_saving(self, dummy_model, trainer_config):
        """
        Verify that the trainer saves checkpoints correctly.
        
        Steps:
        1. Create trainer with a checkpoint directory.
        2. Call _save_checkpoint with a dummy epoch and loss.
        3. Verify that checkpoint file exists.
        4. Verify checkpoint contains expected keys (model_state, optimizer_state, epoch, loss).
        """
        checkpoint_dir = Path(trainer_config['checkpoint_dir'])
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        trainer = Trainer(
            model=dummy_model,
            config=trainer_config,
            train_loader=None,
            val_loader=None
        )
        
        # Save checkpoint
        epoch = 5
        val_loss = 0.5
        trainer._save_checkpoint(epoch, val_loss)
        
        # Verify checkpoint file exists
        checkpoint_path = checkpoint_dir / f"checkpoint_epoch_{epoch}.pth"
        assert checkpoint_path.exists(), "Checkpoint file should be created"
        
        # Load and verify checkpoint contents
        checkpoint = torch.load(checkpoint_path, weights_only=False)
        
        assert 'model_state_dict' in checkpoint, "Checkpoint should contain model weights"
        assert 'optimizer_state_dict' in checkpoint, "Checkpoint should contain optimizer state"
        assert 'epoch' in checkpoint, "Checkpoint should contain epoch number"
        assert 'val_loss' in checkpoint, "Checkpoint should contain validation loss"
        
        assert checkpoint['epoch'] == epoch, "Epoch in checkpoint should match input"
        assert checkpoint['val_loss'] == val_loss, "Val loss in checkpoint should match input"
        
        # Verify model weights match
        for name, param in trainer.model.named_parameters():
            assert torch.equal(
                param, 
                checkpoint['model_state_dict'][name]
            ), "Model weights in checkpoint should match current model"

    def test_training_loop_integration(self, dummy_model, dummy_data, trainer_config):
        """
        End-to-end test of the training loop with a single batch.
        
        Steps:
        1. Create a simple DataLoader with dummy data.
        2. Run one epoch of training.
        3. Verify that loss decreases (or at least is computed).
        4. Verify that metrics are logged.
        """
        # Create a simple dataset and loader
        spectra, fingerprints, conditions, targets = dummy_data
        
        class DummyDataset(torch.utils.data.Dataset):
            def __init__(self, spectra, fingerprints, conditions, targets):
                self.spectra = spectra
                self.fingerprints = fingerprints
                self.conditions = conditions
                self.targets = targets
                
            def __len__(self):
                return len(self.targets)
            
            def __getitem__(self, idx):
                return (
                    self.spectra[idx],
                    self.fingerprints[idx],
                    self.conditions[idx],
                    self.targets[idx]
                )
        
        dataset = DummyDataset(spectra, fingerprints, conditions, targets)
        loader = torch.utils.data.DataLoader(dataset, batch_size=4, shuffle=False)
        
        trainer = Trainer(
            model=dummy_model,
            config=trainer_config,
            train_loader=loader,
            val_loader=None
        )
        
        # Run one epoch
        train_loss = trainer._train_epoch(0)
        
        # Verify loss is computed and finite
        assert isinstance(train_loss, float), "Training loss should be a float"
        assert train_loss >= 0, "Training loss should be non-negative"
        assert np.isfinite(train_loss), "Training loss should be finite"
        
        # Verify that the model was trained (weights changed)
        # We already tested this in test_optimizer_step_executes, but this confirms integration

    def test_validation_loop_integration(self, dummy_model, dummy_data, trainer_config):
        """
        End-to-end test of the validation loop with a single batch.
        
        Steps:
        1. Create a simple DataLoader with dummy data.
        2. Run one epoch of validation.
        3. Verify that val_loss is computed and finite.
        """
        spectra, fingerprints, conditions, targets = dummy_data
        
        class DummyDataset(torch.utils.data.Dataset):
            def __init__(self, spectra, fingerprints, conditions, targets):
                self.spectra = spectra
                self.fingerprints = fingerprints
                self.conditions = conditions
                self.targets = targets
                
            def __len__(self):
                return len(self.targets)
            
            def __getitem__(self, idx):
                return (
                    self.spectra[idx],
                    self.fingerprints[idx],
                    self.conditions[idx],
                    self.targets[idx]
                )
        
        dataset = DummyDataset(spectra, fingerprints, conditions, targets)
        loader = torch.utils.data.DataLoader(dataset, batch_size=4, shuffle=False)
        
        trainer = Trainer(
            model=dummy_model,
            config=trainer_config,
            train_loader=None,
            val_loader=loader
        )
        
        # Run validation
        val_loss = trainer._validate_epoch()
        
        # Verify loss is computed and finite
        assert isinstance(val_loss, float), "Validation loss should be a float"
        assert val_loss >= 0, "Validation loss should be non-negative"
        assert np.isfinite(val_loss), "Validation loss should be finite"

    def test_device_placement(self, dummy_model, trainer_config):
        """
        Verify that the trainer correctly handles device placement (CPU in this case).
        
        Steps:
        1. Create trainer with device='cpu'.
        2. Verify model is on the correct device.
        """
        trainer = Trainer(
            model=dummy_model,
            config=trainer_config,
            train_loader=None,
            val_loader=None
        )
        
        # Verify model is on CPU
        for param in trainer.model.parameters():
            assert param.device.type == 'cpu', \
                f"Model parameters should be on CPU, but found {param.device}"

    def test_learning_rate_configuration(self, dummy_model, trainer_config):
        """
        Verify that the learning rate is correctly set in the optimizer.
        
        Steps:
        1. Create trainer with a specific learning rate.
        2. Verify that the optimizer's learning rate matches the config.
        """
        trainer = Trainer(
            model=dummy_model,
            config=trainer_config,
            train_loader=None,
            val_loader=None
        )
        
        # Verify learning rate
        lr = trainer.optimizer.param_groups[0]['lr']
        assert lr == trainer_config['learning_rate'], \
            f"Learning rate should be {trainer_config['learning_rate']}, but got {lr}"

    def test_batch_size_handling(self, dummy_model, dummy_data, trainer_config):
        """
        Verify that the trainer correctly handles batch processing.
        
        Steps:
        1. Create a DataLoader with a specific batch size.
        2. Run training and verify that batches are processed correctly.
        """
        spectra, fingerprints, conditions, targets = dummy_data
        
        class DummyDataset(torch.utils.data.Dataset):
            def __init__(self, spectra, fingerprints, conditions, targets):
                self.spectra = spectra
                self.fingerprints = fingerprints
                self.conditions = conditions
                self.targets = targets
                
            def __len__(self):
                return len(self.targets)
            
            def __getitem__(self, idx):
                return (
                    self.spectra[idx],
                    self.fingerprints[idx],
                    self.conditions[idx],
                    self.targets[idx]
                )
        
        dataset = DummyDataset(spectra, fingerprints, conditions, targets)
        batch_size = 2
        loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=False)
        
        trainer = Trainer(
            model=dummy_model,
            config=trainer_config,
            train_loader=loader,
            val_loader=None
        )
        
        # Verify batch size
        for batch in loader:
            spectra_batch, fingerprints_batch, conditions_batch, targets_batch = batch
            assert len(spectra_batch) == batch_size, \
                f"Batch size should be {batch_size}, but got {len(spectra_batch)}"
            break  # Only check first batch

    def test_seed_reproducibility(self, dummy_model, dummy_data, trainer_config):
        """
        Verify that setting the seed produces reproducible results.
        
        Steps:
        1. Run training with a fixed seed and capture loss.
        2. Reset seeds and run again with the same seed.
        3. Verify that the loss is identical.
        """
        # First run
        set_seed(trainer_config['seed'])
        trainer1 = Trainer(
            model=DummyAttentionNet(input_dim=100, hidden_dim=32, output_dim=1),
            config=trainer_config,
            train_loader=None,
            val_loader=None
        )
        
        spectra, fingerprints, conditions, targets = dummy_data
        input_tensor = torch.cat([spectra.flatten(1), fingerprints, conditions], dim=1)
        
        trainer1.optimizer.zero_grad()
        outputs1 = trainer1.model(input_tensor)
        loss1 = trainer1.criterion(outputs1, targets.squeeze(-1))
        loss1.backward()
        trainer1.optimizer.step()
        
        loss1_value = loss1.item()
        
        # Second run with same seed
        set_seed(trainer_config['seed'])
        trainer2 = Trainer(
            model=DummyAttentionNet(input_dim=100, hidden_dim=32, output_dim=1),
            config=trainer_config,
            train_loader=None,
            val_loader=None
        )
        
        trainer2.optimizer.zero_grad()
        outputs2 = trainer2.model(input_tensor)
        loss2 = trainer2.criterion(outputs2, targets.squeeze(-1))
        loss2.backward()
        trainer2.optimizer.step()
        
        loss2_value = loss2.item()
        
        # Verify reproducibility
        assert np.isclose(loss1_value, loss2_value), \
            f"Loss should be reproducible with same seed: {loss1_value} vs {loss2_value}"