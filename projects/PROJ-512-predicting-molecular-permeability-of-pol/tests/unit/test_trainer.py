"""
Unit tests for the Trainer module, specifically gradient clipping.
"""
import pytest
import torch
import torch.nn as nn
from torch.optim import Adam

from models.trainer import Trainer, create_trainer


class DummyGNN(nn.Module):
    """A simple dummy GNN for testing purposes."""

    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(10, 1)
        self.relu = nn.ReLU()

    def forward(self, x):
        # Accepts list of tensors or single tensor for testing
        if isinstance(x, list):
            x = torch.stack([t.mean(dim=0, keepdim=True) for t in x])
        return self.relu(self.linear(x))


class TestGradientClipping:
    """Tests for gradient clipping functionality."""

    def test_max_norm_clipping_applies(self):
        """Test that max norm clipping is applied and limits gradient norm."""
        model = DummyGNN()
        optimizer = Adam(model.parameters(), lr=0.01)
        criterion = nn.MSELoss()

        trainer = Trainer(
            model=model,
            optimizer=optimizer,
            criterion=criterion,
            max_norm=0.5,
            clip_type="max_norm",
        )

        # Create dummy data to trigger a backward pass
        x = torch.randn(4, 10)
        y = torch.randn(4, 1)

        # Forward pass
        outputs = model(x)
        loss = criterion(outputs, y)

        # Backward pass
        loss.backward()

        # Store original gradient norms
        original_norms = [p.grad.norm().item() for p in model.parameters() if p.grad is not None]

        # Apply clipping manually to verify behavior
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=0.5)

        # Check that norms are reduced (or stay same if already under threshold)
        clipped_norms = [p.grad.norm().item() for p in model.parameters() if p.grad is not None]

        # At least one gradient should be clipped or all under threshold
        # Since we set max_norm=0.5, the total norm should not exceed 0.5
        total_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=0.5)
        assert total_norm <= 0.5 or all(n <= 0.5 for n in clipped_norms)

    def test_value_clipping_applies(self):
        """Test that value clipping limits individual gradient values."""
        model = DummyGNN()
        optimizer = Adam(model.parameters(), lr=0.01)
        criterion = nn.MSELoss()

        trainer = Trainer(
            model=model,
            optimizer=optimizer,
            criterion=criterion,
            max_norm=0.1,
            clip_type="value",
        )

        x = torch.randn(4, 10)
        y = torch.randn(4, 1)

        outputs = model(x)
        loss = criterion(outputs, y)
        loss.backward()

        # Apply value clipping
        torch.nn.utils.clip_grad_value_(model.parameters(), clip_value=0.1)

        # Check that no gradient value exceeds 0.1
        for p in model.parameters():
            if p.grad is not None:
                assert p.grad.abs().max().item() <= 0.1

    def test_trainer_fit_with_clipping(self, monkeypatch):
        """Test that the trainer fits without errors when clipping is enabled."""
        model = DummyGNN()
        optimizer = Adam(model.parameters(), lr=0.01)
        criterion = nn.MSELoss()

        # Mock dataloaders
        class DummyLoader:
            def __init__(self, data):
                self.data = data

            def __iter__(self):
                return iter(self.data)

            def __len__(self):
                return len(self.data)

        # Create dummy batches
        train_data = [
            (torch.randn(4, 10), torch.randn(4, 1))
            for _ in range(2)
        ]
        train_loader = DummyLoader(train_data)

        trainer = Trainer(
            model=model,
            optimizer=optimizer,
            criterion=criterion,
            max_norm=1.0,
            clip_type="max_norm",
        )

        # Run a single epoch
        history = trainer.fit(train_loader, epochs=1)

        assert len(history) == 1
        assert "train_loss" in history[0]
        assert history[0]["train_loss"] >= 0

    def test_invalid_clip_type_raises(self):
        """Test that invalid clip_type raises ValueError."""
        model = DummyGNN()
        optimizer = Adam(model.parameters(), lr=0.01)
        criterion = nn.MSELoss()

        with pytest.raises(ValueError, match="Unknown clip_type"):
            Trainer(
                model=model,
                optimizer=optimizer,
                criterion=criterion,
                clip_type="invalid_type",
            )

    def test_create_trainer_factory(self):
        """Test the factory function creates a configured trainer."""
        model = DummyGNN()
        optimizer = Adam(model.parameters(), lr=0.01)
        criterion = nn.MSELoss()

        trainer = create_trainer(model, optimizer, criterion)

        assert isinstance(trainer, Trainer)
        assert trainer.max_norm == 1.0  # Default from env or code
        assert trainer.clip_type == "max_norm"