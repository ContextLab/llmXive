"""
Integration test for baseline training pipeline with gradient logging.

This test explicitly runs the baseline model with log_gradient_norms enabled
to populate data/logs/gradient_norms.json for SC-002 verification.

DEPENDS ON: T010b (log_gradient_norms implementation)
"""
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import torch
import torch.nn as nn

# Project imports
from src.training.homeostasis import log_gradient_norms
from src.models.baseline_transformer import BaselineTransformer
from src.training.trainer import TrainingConfig, run_training
from src.data.benchmarks import generate_training_data, generate_test_data, verify_independence


class TestBaselineGradientLogging:
    """
    Integration test verifying that the baseline training pipeline
    correctly logs gradient norms to data/logs/gradient_norms.json.
    """

    @pytest.fixture(autouse=True)
    def setup_temp_dirs(self, tmp_path):
        """Setup temporary directories for logs and results."""
        self.log_dir = tmp_path / "logs"
        self.log_dir.mkdir()
        self.results_dir = tmp_path / "results"
        self.results_dir.mkdir()
        self.data_dir = tmp_path / "data"
        self.data_dir.mkdir()

        # Store original paths to restore later
        self.original_log_dir = None

        # Patch the log path used by log_gradient_norms
        # We need to ensure the function writes to our temp directory
        self.log_path = self.log_dir / "gradient_norms.json"

    def test_gradient_logging_enabled(self):
        """
        Test that running the baseline training with logging enabled
        produces the expected gradient_norms.json file with valid content.
        """
        # Generate synthetic data
        train_data = generate_training_data(num_samples=100, seed=42)
        test_data = generate_test_data(num_samples=50, seed=123)

        # Verify independence
        assert verify_independence(train_data, test_data), "Data distributions must be independent"

        # Create a simple baseline model
        model = BaselineTransformer(
            input_dim=train_data.shape[1],
            hidden_dim=32,
            num_layers=2,
            num_heads=4,
            dropout=0.1
        )

        # Create training configuration
        config = TrainingConfig(
            num_epochs=3,
            batch_size=16,
            learning_rate=0.001,
            log_gradient_norms=True,
            log_path=str(self.log_dir),
            seed=42
        )

        # Prepare data loaders
        train_dataset = torch.utils.data.TensorDataset(
            torch.tensor(train_data, dtype=torch.float32),
            torch.tensor(train_data, dtype=torch.float32)  # Auto-encoder setup
        )
        test_dataset = torch.utils.data.TensorDataset(
            torch.tensor(test_data, dtype=torch.float32),
            torch.tensor(test_data, dtype=torch.float32)
        )

        train_loader = torch.utils.data.DataLoader(
            train_dataset, batch_size=config.batch_size, shuffle=True
        )
        test_loader = torch.utils.data.DataLoader(
            test_dataset, batch_size=config.batch_size, shuffle=False
        )

        optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)

        # Run training
        run_training(
            model=model,
            train_loader=train_loader,
            test_loader=test_loader,
            optimizer=optimizer,
            config=config
        )

        # Verify that gradient_norms.json was created
        assert self.log_path.exists(), f"Gradient log file not created at {self.log_path}"

        # Load and validate the JSON content
        with open(self.log_path, 'r') as f:
            log_data = json.load(f)

        # Verify schema
        assert isinstance(log_data, list), "Log data must be a list of entries"
        assert len(log_data) > 0, "Log data must contain at least one entry"

        # Validate each entry has required fields
        for entry in log_data:
            assert "step" in entry, "Each entry must have a 'step' field"
            assert "gradient_norm" in entry, "Each entry must have a 'gradient_norm' field"
            assert isinstance(entry["step"], int), "'step' must be an integer"
            assert isinstance(entry["gradient_norm"], (int, float)), "'gradient_norm' must be numeric"

        # Verify that multiple steps were logged (at least one per epoch)
        steps_logged = [entry["step"] for entry in log_data]
        assert len(set(steps_logged)) >= config.num_epochs, \
            f"Expected at least {config.num_epochs} unique steps logged, got {len(set(steps_logged))}"

        print(f"✓ Gradient logging test passed. Logged {len(log_data)} entries to {self.log_path}")

    def test_gradient_logging_disabled(self):
        """
        Test that when log_gradient_norms is disabled, no log file is created.
        """
        # Generate synthetic data
        train_data = generate_training_data(num_samples=50, seed=42)

        # Create a simple baseline model
        model = BaselineTransformer(
            input_dim=train_data.shape[1],
            hidden_dim=16,
            num_layers=1,
            num_heads=2,
            dropout=0.1
        )

        # Create training configuration with logging disabled
        config = TrainingConfig(
            num_epochs=2,
            batch_size=16,
            learning_rate=0.001,
            log_gradient_norms=False,
            log_path=str(self.log_dir),
            seed=42
        )

        # Prepare data loaders
        train_dataset = torch.utils.data.TensorDataset(
            torch.tensor(train_data, dtype=torch.float32),
            torch.tensor(train_data, dtype=torch.float32)
        )
        train_loader = torch.utils.data.DataLoader(
            train_dataset, batch_size=config.batch_size, shuffle=True
        )

        optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)

        # Run training
        run_training(
            model=model,
            train_loader=train_loader,
            test_loader=None,
            optimizer=optimizer,
            config=config
        )

        # Verify that gradient_norms.json was NOT created
        assert not self.log_path.exists(), \
            f"Gradient log file should not be created when logging is disabled"

        print("✓ Gradient logging disabled test passed. No log file created.")

    def test_log_gradient_norms_direct_function(self):
        """
        Direct test of the log_gradient_norms function to ensure it writes
        correctly formatted JSON.
        """
        # Create a dummy model
        model = nn.Linear(10, 5)

        # Simulate some gradients
        for param in model.parameters():
            param.grad = torch.randn_like(param)

        # Call the logging function
        log_gradient_norms(model, step=1, log_dir=str(self.log_dir))

        # Verify file was created
        log_path = self.log_dir / "gradient_norms.json"
        assert log_path.exists(), "log_gradient_norms should create the JSON file"

        # Verify content
        with open(log_path, 'r') as f:
            content = json.load(f)

        assert isinstance(content, list), "Content must be a list"
        assert len(content) == 1, "Should have one entry for this call"
        assert content[0]["step"] == 1, "Step should be 1"
        assert "gradient_norm" in content[0], "Entry should have gradient_norm"

        print("✓ Direct log_gradient_norms function test passed.")

    def test_gradient_norms_accumulation(self):
        """
        Test that multiple calls to log_gradient_norms accumulate entries
        in the JSON file rather than overwriting.
        """
        model = nn.Linear(8, 4)

        # First call
        for param in model.parameters():
            param.grad = torch.randn_like(param)
        log_gradient_norms(model, step=1, log_dir=str(self.log_dir))

        # Second call
        for param in model.parameters():
            param.grad = torch.randn_like(param) * 2
        log_gradient_norms(model, step=2, log_dir=str(self.log_dir))

        # Third call
        for param in model.parameters():
            param.grad = torch.randn_like(param) * 0.5
        log_gradient_norms(model, step=3, log_dir=str(self.log_dir))

        # Verify all entries are present
        log_path = self.log_dir / "gradient_norms.json"
        with open(log_path, 'r') as f:
            content = json.load(f)

        assert len(content) == 3, f"Expected 3 entries, got {len(content)}"
        steps = [entry["step"] for entry in content]
        assert steps == [1, 2, 3], f"Expected steps [1, 2, 3], got {steps}"

        # Verify gradient norms are different (reflecting different gradient magnitudes)
        norms = [entry["gradient_norm"] for entry in content]
        assert norms[1] > norms[0] * 1.5, "Second norm should be larger (2x gradients)"
        assert norms[2] < norms[0], "Third norm should be smaller (0.5x gradients)"

        print("✓ Gradient norms accumulation test passed.")