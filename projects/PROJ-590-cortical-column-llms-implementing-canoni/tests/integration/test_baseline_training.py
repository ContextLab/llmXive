"""
Integration test for baseline training pipeline.
Specifically tests that log_gradient_norms is enabled and populates
data/logs/gradient_norms.json for SC-002 verification.
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
import sys
import torch
import torch.nn as nn

# Add project root to path if not already present
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.training.trainer import TrainingConfig, run_training
from src.models.baseline_transformer import BaselineTransformer
from src.data.benchmarks import generate_training_data, generate_test_data
from src.training.homeostasis import log_gradient_norms, HomeostasisConfig
from src.experiments.baseline_runner import ExperimentConfig, BaselineRunner


class TestBaselineTrainingGradientLogging:
    """Tests that baseline training explicitly logs gradient norms."""

    def test_baseline_logs_gradient_norms_to_disk(self, tmp_path):
        """
        Runs a minimal baseline training session with log_gradient_norms enabled
        and verifies that data/logs/gradient_norms.json is created and populated.
        """
        # Setup paths relative to tmp_path to simulate project structure
        # We need to ensure the log path matches the expected project location
        # For the test, we will configure the runner to write to tmp_path/logs
        # but verify the file content schema matches the requirement.
        
        # However, the task requires populating `data/logs/gradient_norms.json`.
        # In a real execution, this is relative to the project root.
        # Here we use tmp_path to ensure we don't pollute the repo, 
        # but we will assert the file is written to the configured log dir.
        
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # 1. Generate synthetic data
        train_data = generate_training_data(n_samples=100, n_features=10)
        test_data = generate_test_data(n_samples=50, n_features=10)
        
        # 2. Configure Homeostasis to enable logging
        # The log_gradient_norms function writes to a specific path.
        # We need to ensure the config points to our temp logs dir.
        # Since log_gradient_norms is a function that writes to a hardcoded path 
        # in the production code (usually relative to project root), we need to 
        # verify that the *call* happens and writes to the expected location 
        # relative to the execution context.
        
        # To make this test robust and portable, we will patch the log path
        # or assume the project root is set correctly. 
        # Given the constraints, we will run the training and check the file
        # at the path defined in the production code (data/logs/gradient_norms.json)
        # BUT since we are in a temp dir, we must adapt.
        
        # Strategy: We will run the training with a custom config that sets the 
        # log directory to tmp_path/logs, and verify the file exists there.
        # This validates the *mechanism* of logging.
        
        # Create a minimal model
        model = BaselineTransformer(input_dim=10, hidden_dim=32, output_dim=1)
        
        # Configure training
        train_cfg = TrainingConfig(
            epochs=2,
            batch_size=16,
            learning_rate=0.01,
            log_interval=1,
            enable_gradient_logging=True,
            log_dir=str(logs_dir)  # Point to our temp logs dir
        )
        
        # 3. Run training
        # We pass the model, data, and config
        # The run_training function should call log_gradient_norms internally
        metrics = run_training(
            model=model,
            train_data=train_data,
            test_data=test_data,
            config=train_cfg
        )
        
        # 4. Verify the log file exists
        log_file_path = logs_dir / "gradient_norms.json"
        assert log_file_path.exists(), f"Gradient norms log file not found at {log_file_path}"
        
        # 5. Verify the content is valid JSON and has the expected schema
        with open(log_file_path, 'r') as f:
            log_data = json.load(f)
        
        assert isinstance(log_data, list), "Gradient norms log must be a list of entries"
        assert len(log_data) > 0, "Gradient norms log must contain at least one entry"
        
        # Check schema of first entry
        first_entry = log_data[0]
        assert "step" in first_entry, "Entry must have 'step'"
        assert "layer_name" in first_entry, "Entry must have 'layer_name'"
        assert "norm" in first_entry, "Entry must have 'norm'"
        assert isinstance(first_entry["step"], int), "Step must be int"
        assert isinstance(first_entry["norm"], float), "Norm must be float"
        
        # 6. Verify that the log_gradient_norms function was actually called
        # by checking that we have entries for multiple steps/layers
        steps = [entry["step"] for entry in log_data]
        # We ran 2 epochs, so we expect entries for at least step 1 and 2 (or similar)
        # The exact number depends on the training loop implementation
        assert len(steps) >= 2, "Expected gradient logs for multiple steps"

    def test_log_file_schema_compliance(self, tmp_path):
        """
        Verifies the exact schema required for SC-002 verification.
        """
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Create a dummy log file that mimics the expected output
        # to verify the schema validator logic if it existed.
        # Instead, we generate real data via a minimal run.
        
        model = BaselineTransformer(input_dim=5, hidden_dim=16, output_dim=1)
        train_data = generate_training_data(n_samples=20, n_features=5)
        test_data = generate_test_data(n_samples=10, n_features=5)
        
        train_cfg = TrainingConfig(
            epochs=1,
            batch_size=10,
            learning_rate=0.01,
            log_interval=1,
            enable_gradient_logging=True,
            log_dir=str(logs_dir)
        )
        
        run_training(model=model, train_data=train_data, test_data=test_data, config=train_cfg)
        
        log_file = logs_dir / "gradient_norms.json"
        assert log_file.exists()
        
        with open(log_file, 'r') as f:
            data = json.load(f)
        
        # Verify schema constraints
        for entry in data:
            assert "step" in entry
            assert "layer_name" in entry
            assert "norm" in entry
            assert entry["norm"] >= 0.0  # Norms are non-negative
            
        # Verify it's not empty
        assert len(data) > 0

    def test_gradient_logging_disabled(self, tmp_path):
        """
        Verifies that when logging is disabled, no file is created (or empty).
        """
        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        model = BaselineTransformer(input_dim=5, hidden_dim=16, output_dim=1)
        train_data = generate_training_data(n_samples=20, n_features=5)
        test_data = generate_test_data(n_samples=10, n_features=5)
        
        train_cfg = TrainingConfig(
            epochs=1,
            batch_size=10,
            learning_rate=0.01,
            log_interval=1,
            enable_gradient_logging=False, # Explicitly disabled
            log_dir=str(logs_dir)
        )
        
        run_training(model=model, train_data=train_data, test_data=test_data, config=train_cfg)
        
        log_file = logs_dir / "gradient_norms.json"
        # If logging is disabled, the file should either not exist or be empty
        if log_file.exists():
            with open(log_file, 'r') as f:
                content = f.read()
            assert len(content.strip()) == 0 or content == "[]", "Log file should be empty when logging is disabled"

# Note: The actual path `data/logs/gradient_norms.json` is handled by the 
# run_baseline_training.py script or the production runner which sets the 
# working directory or log path appropriately. This test verifies the 
# functionality and schema compliance in a controlled temp environment.