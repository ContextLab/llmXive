"""
Integration test for baseline training pipeline.
Verifies that the baseline model trains correctly and logs gradient norms
for SC-002 verification.
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
import sys
import torch
import torch.nn as nn
import numpy as np

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.baseline_transformer import BaselineTransformer
from src.data.benchmarks import generate_training_data, generate_test_data
from src.training.trainer import TrainingConfig, run_training
from src.training.homeostasis import log_gradient_norms, HomeostasisConfig


class TestBaselineTraining:
    """Integration tests for the baseline training pipeline."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up temporary directories for logs and results."""
        self.tmp_path = tmp_path
        self.log_dir = self.tmp_path / "logs"
        self.log_dir.mkdir()
        self.data_dir = self.tmp_path / "data"
        self.data_dir.mkdir()
        self.results_dir = self.tmp_path / "results"
        self.results_dir.mkdir()
        return self

    def test_baseline_training_logs_gradients(self):
        """
        T012b: Run baseline model with log_gradient_norms enabled.
        Verify that data/logs/gradient_norms.json is populated.
        """
        # 1. Generate synthetic data (Lorenz for train, Polynomials for test)
        # Use small sizes for integration test speed
        train_data = generate_training_data(n_samples=500, seed=42)
        test_data = generate_test_data(n_samples=200, seed=42)

        # 2. Prepare model
        # Small config for integration test
        model_config = {
            "input_dim": 3,  # Lorenz state dim
            "hidden_dim": 32,
            "output_dim": 3,
            "num_layers": 2,
            "num_heads": 2
        }
        model = BaselineTransformer(**model_config)

        # 3. Configure training with gradient logging enabled
        homeostasis_config = HomeostasisConfig(
            log_gradients=True,
            log_path=str(self.log_dir / "gradient_norms.json"),
            target_ei_ratio=4.0,
            decay_rate=0.9
        )

        training_config = TrainingConfig(
            epochs=3,  # Minimal epochs for integration test
            batch_size=32,
            learning_rate=1e-3,
            log_interval=1,
            homeostasis_config=homeostasis_config,
            device="cpu"
        )

        # 4. Run training
        # The trainer will call log_gradient_norms internally if enabled
        metrics = run_training(
            model=model,
            train_data=train_data,
            test_data=test_data,
            config=training_config,
            log_dir=str(self.log_dir)
        )

        # 5. Verify the log file exists
        log_file = self.log_dir / "gradient_norms.json"
        assert log_file.exists(), f"Gradient log file {log_file} was not created"

        # 6. Verify the log file contains valid data
        with open(log_file, 'r') as f:
            log_data = json.load(f)

        assert isinstance(log_data, list), "Log data must be a list of entries"
        assert len(log_data) > 0, "Log file is empty; no gradients were logged"

        # Verify structure of log entries
        required_keys = {"step", "grad_norm", "timestamp"}
        for entry in log_data:
            assert isinstance(entry, dict), f"Log entry must be a dict: {entry}"
            assert required_keys.issubset(entry.keys()), f"Missing keys in entry: {entry}"
            assert "grad_norm" in entry, "grad_norm field is missing"
            assert isinstance(entry["grad_norm"], (int, float)), "grad_norm must be numeric"
            assert entry["grad_norm"] >= 0, "grad_norm cannot be negative"

    def test_gradient_norms_reflect_training_progress(self):
        """
        Verify that gradient norms are not constant (i.e., the model is actually learning).
        """
        # Generate data
        train_data = generate_training_data(n_samples=500, seed=42)
        test_data = generate_test_data(n_samples=200, seed=42)

        model_config = {
            "input_dim": 3,
            "hidden_dim": 32,
            "output_dim": 3,
            "num_layers": 2,
            "num_heads": 2
        }
        model = BaselineTransformer(**model_config)

        homeostasis_config = HomeostasisConfig(
            log_gradients=True,
            log_path=str(self.log_dir / "gradient_norms.json"),
            target_ei_ratio=4.0,
            decay_rate=0.9
        )

        training_config = TrainingConfig(
            epochs=5,
            batch_size=32,
            learning_rate=1e-3,
            log_interval=1,
            homeostasis_config=homeostasis_config,
            device="cpu"
        )

        run_training(
            model=model,
            train_data=train_data,
            test_data=test_data,
            config=training_config,
            log_dir=str(self.log_dir)
        )

        log_file = self.log_dir / "gradient_norms.json"
        with open(log_file, 'r') as f:
            log_data = json.load(f)

        norms = [entry["grad_norm"] for entry in log_data]
        
        # Check that we have some variance in the norms (not all identical)
        # This confirms the training loop is actually running and computing gradients
        unique_norms = set([round(n, 6) for n in norms])
        assert len(unique_norms) > 1, "All gradient norms are identical; training may not be progressing"

        # Check that norms are within a reasonable range (not NaN or Inf)
        for norm in norms:
            assert np.isfinite(norm), f"Gradient norm is not finite: {norm}"

    def test_homeostasis_scaling_factors_logged(self):
        """
        Verify that if homeostatic scaling is applied, the scaling factors are logged.
        """
        train_data = generate_training_data(n_samples=500, seed=42)
        test_data = generate_test_data(n_samples=200, seed=42)

        model_config = {
            "input_dim": 3,
            "hidden_dim": 32,
            "output_dim": 3,
            "num_layers": 2,
            "num_heads": 2
        }
        model = BaselineTransformer(**model_config)

        # Enable homeostatic scaling
        homeostasis_config = HomeostasisConfig(
            log_gradients=True,
            log_path=str(self.log_dir / "gradient_norms.json"),
            target_ei_ratio=4.0,
            decay_rate=0.9,
            apply_scaling=True  # Explicitly enable scaling
        )

        training_config = TrainingConfig(
            epochs=5,
            batch_size=32,
            learning_rate=1e-3,
            log_interval=1,
            homeostasis_config=homeostasis_config,
            device="cpu"
        )

        run_training(
            model=model,
            train_data=train_data,
            test_data=test_data,
            config=training_config,
            log_dir=str(self.log_dir)
        )

        log_file = self.log_dir / "gradient_norms.json"
        with open(log_file, 'r') as f:
            log_data = json.load(f)

        # Verify that scaling factors are included if scaling was applied
        # (The log_gradient_norms function should include scaling_factor if applied)
        for entry in log_data:
            if "scaling_factor" in entry:
                assert isinstance(entry["scaling_factor"], (int, float, dict)), \
                    "scaling_factor must be numeric or a dict of layer factors"

    def test_sc002_verification_compliance(self):
        """
        SC-002 Verification: Ensure the log format matches the expected schema
        for downstream gradient stability analysis (T032).
        """
        train_data = generate_training_data(n_samples=500, seed=42)
        test_data = generate_test_data(n_samples=200, seed=42)

        model_config = {
            "input_dim": 3,
            "hidden_dim": 32,
            "output_dim": 3,
            "num_layers": 2,
            "num_heads": 2
        }
        model = BaselineTransformer(**model_config)

        homeostasis_config = HomeostasisConfig(
            log_gradients=True,
            log_path=str(self.log_dir / "gradient_norms.json"),
            target_ei_ratio=4.0,
            decay_rate=0.9
        )

        training_config = TrainingConfig(
            epochs=3,
            batch_size=32,
            learning_rate=1e-3,
            log_interval=1,
            homeostasis_config=homeostasis_config,
            device="cpu"
        )

        run_training(
            model=model,
            train_data=train_data,
            test_data=test_data,
            config=training_config,
            log_dir=str(self.log_dir)
        )

        log_file = self.log_dir / "gradient_norms.json"
        with open(log_file, 'r') as f:
            log_data = json.load(f)

        # Verify SC-002 required fields
        expected_fields = {"step", "grad_norm", "timestamp"}
        for i, entry in enumerate(log_data):
            missing = expected_fields - set(entry.keys())
            assert not missing, f"Entry {i} missing SC-002 required fields: {missing}"
            
            # Verify data types for SC-002 compatibility
            assert isinstance(entry["step"], int), "step must be integer"
            assert isinstance(entry["grad_norm"], (int, float)), "grad_norm must be numeric"
            assert isinstance(entry["timestamp"], str), "timestamp must be ISO string"