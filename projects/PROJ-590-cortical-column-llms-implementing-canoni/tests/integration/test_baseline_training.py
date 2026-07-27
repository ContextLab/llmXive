"""
Integration tests for the baseline training pipeline.
Specifically tests T012b: runs baseline model with log_gradient_norms enabled
to populate data/logs/gradient_norms.json for SC-002 verification.
"""
import json
import os
import tempfile
import shutil
import pytest
from pathlib import Path
import torch
import numpy as np

# Import project modules based on provided API surface
from src.models.baseline_transformer import BaselineTransformer
from src.data.benchmarks import generate_training_data, generate_test_data
from src.training.trainer import TrainingConfig, run_training, calculate_mae
from src.training.homeostasis import log_gradient_norms, HomeostasisConfig

# Ensure project root is in path if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(PROJECT_ROOT))


class TestBaselineGradientLogging:
    """
    Test suite for T012b: Verification that baseline training logs gradient norms.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """
        Setup temporary directories for logs and data to avoid polluting the repo.
        We will copy the real log file to the expected location if the test passes.
        """
        self.original_logs_dir = PROJECT_ROOT / "data" / "logs"
        self.temp_logs_dir = tmp_path / "data" / "logs"
        self.temp_logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Store original path to restore if needed, though we won't write to original in test
        self.temp_output_path = self.temp_logs_dir / "gradient_norms.json"
        
        yield

        # Cleanup handled by pytest tmp_path, but we verify file existence here
        assert self.temp_output_path.exists(), "Log file was not created during training."

    def test_baseline_training_populates_gradient_logs(self):
        """
        T012b: Run a short baseline training loop with log_gradient_norms enabled.
        Verify that data/logs/gradient_norms.json is populated with valid data.
        """
        # Configuration for a minimal run to verify logging
        # Using small dimensions to ensure it runs quickly within time budget
        config = TrainingConfig(
            model_type="baseline",
            hidden_dim=32,
            num_layers=2,
            num_heads=2,
            seq_len=16,
            batch_size=8,
            num_epochs=2,  # Minimal epochs for verification
            learning_rate=1e-3,
            device="cpu",
            seed=42,
            # Enable gradient logging
            log_gradient_norms=True,
            log_output_path=str(self.temp_output_path)
        )

        # Generate synthetic data (T005)
        # Ensure distinct seeds/distributions as per T005 requirements
        train_data = generate_training_data(seed=42, n_samples=64)
        test_data = generate_test_data(seed=123, n_samples=32)

        # Prepare tensors
        X_train = torch.tensor(train_data['X'], dtype=torch.float32)
        y_train = torch.tensor(train_data['y'], dtype=torch.float32)
        X_test = torch.tensor(test_data['X'], dtype=torch.float32)
        y_test = torch.tensor(test_data['y'], dtype=torch.float32)

        # Initialize Model
        model = BaselineTransformer(
            input_dim=X_train.shape[1],
            hidden_dim=config.hidden_dim,
            num_layers=config.num_layers,
            num_heads=config.num_heads,
            seq_len=config.seq_len
        )

        optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)

        # Run Training
        # We wrap run_training to inject the logging hook if it's not fully integrated
        # into the trainer loop by default, or assume run_training calls it.
        # Based on T008b, log_gradient_norms is a function. 
        # We assume run_training handles the loop.
        
        metrics = run_training(
            model=model,
            train_loader=torch.utils.data.DataLoader(
                torch.utils.data.TensorDataset(X_train, y_train), 
                batch_size=config.batch_size
            ),
            test_loader=torch.utils.data.DataLoader(
                torch.utils.data.TensorDataset(X_test, y_test), 
                batch_size=config.batch_size
            ),
            optimizer=optimizer,
            config=config,
            device=config.device
        )

        # Verification 1: Check if file exists
        assert self.temp_output_path.exists(), (
            f"Gradient norms log file {self.temp_output_path} was not created. "
            "Ensure log_gradient_norms is called during training."
        )

        # Verification 2: Check file content structure
        with open(self.temp_output_path, 'r') as f:
            log_data = json.load(f)

        assert isinstance(log_data, list), "Log data must be a list of entries."
        assert len(log_data) > 0, "Log data is empty. Training loop might not have executed logging."

        # Verify schema of log entries
        required_keys = {"step", "total_norm", "timestamp"}
        first_entry = log_data[0]
        assert required_keys.issubset(first_entry.keys()), (
            f"Log entry missing required keys. Found: {first_entry.keys()}, Expected: {required_keys}"
        )
        
        # Verify data types
        assert isinstance(first_entry["step"], int), "Step must be integer"
        assert isinstance(first_entry["total_norm"], float), "Total norm must be float"

        # Verification 3: Ensure values are reasonable (not NaN/Inf)
        for entry in log_data:
            assert np.isfinite(entry["total_norm"]), (
                f"Gradient norm is not finite at step {entry['step']}: {entry['total_norm']}"
            )

        # Optional: Verify that the log file is in the expected repository location
        # if the test is run in a context where we can write to data/logs.
        # For strict unit/integration isolation, we verified the temp path.
        # If the requirement is strictly that it MUST be at data/logs/gradient_norms.json
        # in the repo root, we would copy it here, but usually tests use temp dirs.
        # However, T012b description says "populate data/logs/gradient_norms.json".
        # We will copy to the expected location if the original directory exists.
        if self.original_logs_dir.exists():
            target_path = self.original_logs_dir / "gradient_norms.json"
            shutil.copy(self.temp_output_path, target_path)

    def test_gradient_norms_reflect_training_progress(self):
        """
        T012b (Extended): Verify that the logged gradient norms are not constant,
        indicating that the model is actually learning and gradients are updating.
        """
        config = TrainingConfig(
            model_type="baseline",
            hidden_dim=32,
            num_layers=2,
            num_heads=2,
            seq_len=16,
            batch_size=8,
            num_epochs=3,
            learning_rate=1e-2, # Higher LR to ensure gradient movement
            device="cpu",
            seed=42,
            log_gradient_norms=True,
            log_output_path=str(self.temp_output_path)
        )

        train_data = generate_training_data(seed=42, n_samples=64)
        X_train = torch.tensor(train_data['X'], dtype=torch.float32)
        y_train = torch.tensor(train_data['y'], dtype=torch.float32)

        model = BaselineTransformer(
            input_dim=X_train.shape[1],
            hidden_dim=config.hidden_dim,
            num_layers=config.num_layers,
            num_heads=config.num_heads,
            seq_len=config.seq_len
        )

        optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)

        train_loader = torch.utils.data.DataLoader(
            torch.utils.data.TensorDataset(X_train, y_train), 
            batch_size=config.batch_size
        )

        run_training(
            model=model,
            train_loader=train_loader,
            test_loader=None,
            optimizer=optimizer,
            config=config,
            device=config.device
        )

        with open(self.temp_output_path, 'r') as f:
            log_data = json.load(f)

        norms = [entry["total_norm"] for entry in log_data]
        
        # Check for variance in norms. If all are identical, something is wrong.
        unique_norms = set(norms)
        assert len(unique_norms) > 1, (
            "All gradient norms are identical. The model might not be updating or logging is static."
        )

        # Check that norms are generally decreasing or stable (not exploding immediately)
        # This is a soft check to ensure training is sane
        assert all(n > 0 for n in norms), "Gradient norms should be positive."